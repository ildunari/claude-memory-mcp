#!/bin/bash

# Deployment automation script for Claude Memory MCP System
# Supports local, development, staging, and production deployments

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="memory-mcp"
NAMESPACE="${PROJECT_NAME}"
CHART_PATH="${SCRIPT_DIR}/helm/${PROJECT_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Memory MCP Deployment Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    local       Deploy locally using Docker Compose
    k8s         Deploy to Kubernetes cluster
    helm        Deploy using Helm chart
    build       Build container images
    test        Run tests and validation
    clean       Clean up deployments
    status      Show deployment status
    logs        Show application logs

Options:
    -e, --environment   Environment (dev, staging, prod) [default: dev]
    -n, --namespace     Kubernetes namespace [default: memory-mcp]
    -c, --config        Configuration file path
    -i, --image-tag     Container image tag [default: latest]
    -w, --wait          Wait for deployment to complete
    -f, --force         Force deployment (skip confirmations)
    -d, --dry-run       Show what would be deployed without executing
    -h, --help          Show this help message

Examples:
    $0 local                                    # Deploy locally with Docker Compose
    $0 k8s -e dev -w                           # Deploy to dev Kubernetes
    $0 helm -e prod -i v1.2.3 -w              # Deploy prod with Helm
    $0 build -i latest                         # Build images
    $0 test                                     # Run tests
    $0 status -e staging                       # Check staging status
    $0 clean -e dev                            # Clean up dev environment

EOF
}

# Parse arguments
ENVIRONMENT="dev"
NAMESPACE="${PROJECT_NAME}"
CONFIG_FILE=""
IMAGE_TAG="latest"
WAIT_FOR_DEPLOYMENT=false
FORCE=false
DRY_RUN=false
COMMAND=""

while [[ $# -gt 0 ]]; do
    case $1 in
        local|k8s|helm|build|test|clean|status|logs)
            COMMAND="$1"
            shift
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -i|--image-tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -w|--wait)
            WAIT_FOR_DEPLOYMENT=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

if [[ -z "$COMMAND" ]]; then
    log_error "No command specified"
    show_help
    exit 1
fi

# Environment-specific settings
case $ENVIRONMENT in
    dev|development)
        NAMESPACE="${PROJECT_NAME}-dev"
        DEFAULT_CONFIG="config_migration_enabled.json"
        ;;
    staging)
        NAMESPACE="${PROJECT_NAME}-staging"
        DEFAULT_CONFIG="config.production.json"
        ;;
    prod|production)
        NAMESPACE="${PROJECT_NAME}-prod"
        DEFAULT_CONFIG="config.production.json"
        ;;
    *)
        log_error "Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac

CONFIG_FILE="${CONFIG_FILE:-$DEFAULT_CONFIG}"

# Utility functions
check_prerequisites() {
    local tools=("$@")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is required but not installed"
            exit 1
        fi
    done
}

wait_for_pods() {
    local namespace=$1
    local timeout=${2:-300}
    
    log_info "Waiting for pods to be ready in namespace $namespace..."
    
    if kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=memory-mcp \
        -n "$namespace" --timeout="${timeout}s"; then
        log_success "All pods are ready"
        return 0
    else
        log_error "Pods failed to become ready within ${timeout}s"
        return 1
    fi
}

check_health() {
    local namespace=$1
    local service_name="memory-mcp-service"
    
    log_info "Checking application health..."
    
    # Port forward for health check
    kubectl port-forward -n "$namespace" "service/$service_name" 8080:80 &
    local port_forward_pid=$!
    
    # Wait a moment for port forward to establish
    sleep 3
    
    # Health check
    if curl -f http://localhost:8080/health &> /dev/null; then
        log_success "Application health check passed"
        kill $port_forward_pid
        return 0
    else
        log_error "Application health check failed"
        kill $port_forward_pid
        return 1
    fi
}

# Command implementations
deploy_local() {
    log_info "Deploying Memory MCP locally with Docker Compose..."
    
    check_prerequisites "docker" "docker-compose"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry run - would execute: docker-compose -f docker-compose.production.yml up -d"
        return 0
    fi
    
    # Check if Qdrant is already running
    if ! curl -s http://localhost:6333/health &> /dev/null; then
        log_info "Starting Qdrant..."
        docker-compose -f docker-compose.qdrant.yml up -d qdrant
        
        # Wait for Qdrant to be ready
        local retries=30
        while [[ $retries -gt 0 ]] && ! curl -s http://localhost:6333/health &> /dev/null; do
            log_info "Waiting for Qdrant to be ready... ($retries attempts remaining)"
            sleep 2
            ((retries--))
        done
        
        if [[ $retries -eq 0 ]]; then
            log_error "Qdrant failed to start"
            exit 1
        fi
    fi
    
    # Build and start services
    log_info "Building and starting Memory MCP services..."
    docker-compose -f docker-compose.production.yml build
    docker-compose -f docker-compose.production.yml up -d
    
    if [[ "$WAIT_FOR_DEPLOYMENT" == "true" ]]; then
        log_info "Waiting for services to be healthy..."
        sleep 10
        
        # Check service health
        local retries=30
        while [[ $retries -gt 0 ]]; do
            if curl -f http://localhost:8001/health &> /dev/null; then
                log_success "Memory MCP service is healthy"
                break
            fi
            log_info "Waiting for Memory MCP to be ready... ($retries attempts remaining)"
            sleep 2
            ((retries--))
        done
        
        if [[ $retries -eq 0 ]]; then
            log_error "Memory MCP failed to start"
            exit 1
        fi
    fi
    
    log_success "Local deployment completed successfully"
    log_info "Services available at:"
    log_info "  - Memory MCP Primary: http://localhost:8001"
    log_info "  - Memory MCP Secondary: http://localhost:8002"
    log_info "  - Qdrant: http://localhost:6333"
    log_info "  - Grafana: http://localhost:3000"
    log_info "  - Prometheus: http://localhost:9090"
}

deploy_k8s() {
    log_info "Deploying Memory MCP to Kubernetes..."
    
    check_prerequisites "kubectl"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry run - would apply Kubernetes manifests to namespace $NAMESPACE"
        kubectl apply -f k8s/memory-mcp-deployment.yaml --dry-run=client
        return 0
    fi
    
    # Create namespace if it doesn't exist
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply manifests
    log_info "Applying Kubernetes manifests..."
    kubectl apply -f k8s/memory-mcp-deployment.yaml -n "$NAMESPACE"
    
    if [[ "$WAIT_FOR_DEPLOYMENT" == "true" ]]; then
        wait_for_pods "$NAMESPACE"
        check_health "$NAMESPACE"
    fi
    
    log_success "Kubernetes deployment completed successfully"
}

deploy_helm() {
    log_info "Deploying Memory MCP with Helm..."
    
    check_prerequisites "helm" "kubectl"
    
    # Prepare Helm values
    local values_args=()
    values_args+=(--set "memoryMcp.image.tag=$IMAGE_TAG")
    values_args+=(--set "global.environment=$ENVIRONMENT")
    
    if [[ -n "$CONFIG_FILE" ]] && [[ -f "$CONFIG_FILE" ]]; then
        values_args+=(--set-file "config=$CONFIG_FILE")
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry run - would install Helm chart with values:"
        helm template "$PROJECT_NAME" "$CHART_PATH" \
            --namespace "$NAMESPACE" \
            "${values_args[@]}"
        return 0
    fi
    
    # Install/upgrade with Helm
    log_info "Installing/upgrading Helm chart..."
    helm upgrade --install "$PROJECT_NAME" "$CHART_PATH" \
        --namespace "$NAMESPACE" \
        --create-namespace \
        "${values_args[@]}" \
        ${WAIT_FOR_DEPLOYMENT:+--wait} \
        ${WAIT_FOR_DEPLOYMENT:+--timeout=10m}
    
    if [[ "$WAIT_FOR_DEPLOYMENT" == "true" ]]; then
        check_health "$NAMESPACE"
    fi
    
    log_success "Helm deployment completed successfully"
}

build_images() {
    log_info "Building container images..."
    
    check_prerequisites "docker"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry run - would build image with tag: $IMAGE_TAG"
        return 0
    fi
    
    log_info "Building Memory MCP image..."
    docker build -f Dockerfile.memory-mcp -t "memory-mcp:$IMAGE_TAG" .
    
    log_success "Image built successfully: memory-mcp:$IMAGE_TAG"
}

run_tests() {
    log_info "Running tests and validation..."
    
    check_prerequisites "python3" "pip"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry run - would run test suite"
        return 0
    fi
    
    # Install test dependencies
    pip install -r requirements.txt
    pip install -r requirements-qdrant.txt
    pip install pytest pytest-cov pytest-asyncio
    
    # Run tests
    log_info "Running unit tests..."
    python -m pytest tests/ -v
    
    log_info "Running integration tests..."
    python validate_phase2.py
    
    log_info "Running Phase 2 component tests..."
    python test_phase2_dual_collection.py
    
    log_success "All tests passed"
}

clean_deployment() {
    log_info "Cleaning up deployment..."
    
    case $COMMAND in
        local)
            check_prerequisites "docker-compose"
            if [[ "$DRY_RUN" == "true" ]]; then
                log_info "Dry run - would stop and remove Docker Compose services"
                return 0
            fi
            docker-compose -f docker-compose.production.yml down -v
            log_success "Local deployment cleaned up"
            ;;
        k8s)
            check_prerequisites "kubectl"
            if [[ "$DRY_RUN" == "true" ]]; then
                log_info "Dry run - would delete namespace $NAMESPACE"
                return 0
            fi
            kubectl delete namespace "$NAMESPACE"
            log_success "Kubernetes deployment cleaned up"
            ;;
        helm)
            check_prerequisites "helm"
            if [[ "$DRY_RUN" == "true" ]]; then
                log_info "Dry run - would uninstall Helm release $PROJECT_NAME"
                return 0
            fi
            helm uninstall "$PROJECT_NAME" -n "$NAMESPACE"
            kubectl delete namespace "$NAMESPACE"
            log_success "Helm deployment cleaned up"
            ;;
    esac
}

show_status() {
    log_info "Showing deployment status for environment: $ENVIRONMENT"
    
    case $COMMAND in
        local)
            check_prerequisites "docker-compose"
            docker-compose -f docker-compose.production.yml ps
            ;;
        k8s|helm)
            check_prerequisites "kubectl"
            kubectl get all -n "$NAMESPACE"
            ;;
    esac
}

show_logs() {
    log_info "Showing application logs for environment: $ENVIRONMENT"
    
    case $COMMAND in
        local)
            check_prerequisites "docker-compose"
            docker-compose -f docker-compose.production.yml logs -f memory-mcp-1
            ;;
        k8s|helm)
            check_prerequisites "kubectl"
            kubectl logs -f -l app.kubernetes.io/name=memory-mcp -n "$NAMESPACE"
            ;;
    esac
}

# Main execution
main() {
    log_info "Memory MCP Deployment Script"
    log_info "Command: $COMMAND, Environment: $ENVIRONMENT, Namespace: $NAMESPACE"
    
    if [[ "$FORCE" != "true" ]] && [[ "$ENVIRONMENT" == "production" ]]; then
        read -p "You are deploying to PRODUCTION. Are you sure? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Deployment cancelled"
            exit 0
        fi
    fi
    
    case $COMMAND in
        local)
            deploy_local
            ;;
        k8s)
            deploy_k8s
            ;;
        helm)
            deploy_helm
            ;;
        build)
            build_images
            ;;
        test)
            run_tests
            ;;
        clean)
            clean_deployment
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"