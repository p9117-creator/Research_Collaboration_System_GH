provider "azurerm" {
  features {}
  subscription_id = "c83fbfa2-4756-4cf1-ae75-0b88b13c58db"
}

variable "resource_group_name" {
  default = "research-collab-rg"
}

variable "location" {
  default = "eastus"
}

resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

# Azure Container Registry
resource "azurerm_container_registry" "acr" {
  name                = "researchcollabreg${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic" # Using Basic for better compatibility
  admin_enabled       = true
}

resource "random_string" "suffix" {
  length  = 5
  special = false
  upper   = false
}

# Azure Kubernetes Service (AKS)
resource "azurerm_kubernetes_cluster" "aks" {
  name                = "research-collab-aks"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "researchcollab"

  default_node_pool {
    name       = "default"
    node_count = 2
    vm_size    = "Standard_B2s_v2" # Using your proven VM size
  }

  identity {
    type = "SystemAssigned"
  }

  tags = {
    Environment = "Production"
    Project     = "Research Collaboration System"
  }
}

resource "azurerm_role_assignment" "aks_acr" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id
}

output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.aks.name
}

output "acr_login_server" {
  value = azurerm_container_registry.acr.login_server
}
