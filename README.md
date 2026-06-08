# hardened-k8s-infrastructure
Enterprise-grade Kubernetes deployment pipeline with strict DevSecOps policies and automated Checkov scanning

# Secure GitOps & Kubernetes Infrastructure Pipeline

This repository showcases an enterprise-grade, hardened Kubernetes infrastructure deployment managed via a DevSecOps CI/CD pipeline. The project focuses on the **Shift-Left Security** approach, ensuring zero infrastructure misconfigurations before deployment.

## 🛠️ Tech Stack
* **Orchestration:** Kubernetes (K8s)
* **Security Scanner (IaC):** Checkov (Prisma Cloud)
* **CI/CD Automation:** GitHub Actions
* **Web Server:** Nginx (Unprivileged architecture)

## 🔐 Implemented Security Hardening Features

The Kubernetes configurations have been aggressively hardened and achieve a **0-failure security score** on Checkov audits:

1. **Process Isolation:** Disabled root execution (`runAsNonRoot: true`) using a custom high UID (`10001`).
2. **Immutable File System:** Enabled `readOnlyRootFilesystem: true` to prevent any remote code execution from writing malicious scripts to the container disk. Temporary cache writes are redirected to an ephemeral `emptyDir` in RAM.
3. **Least Privilege Principle:** * Fully stripped Linux kernel privileges using `capabilities.drop: ["ALL"]`.
   * Disabled automatic mounting of core K8s system tokens (`automountServiceAccountToken: false`).
4. **Network Segmentation:** Isolated deployment into a dedicated `secure-prod` Namespace with an strict `NetworkPolicy` firewall blocking unauthorized ingress/egress traffic.
5. **High Availability & Health Checks:** Implemented HTTP `livenessProbe` and `readinessProbe` to allow automated cluster self-healing and zero-downtime rolling updates.

## 🚀 CI/CD Pipeline Workflow

Every time code is pushed to the `main` branch, GitHub Actions automatically executes the following steps:
1. Instantiates a clean runner environment.
2. Checks out the current Infrastructure-as-Code (IaC) configuration.
3. Executes a **Checkov static analysis scan** targeting the `k8s/` directory.
4. Breaks the build immediately if any security vulnerabilities, missing resource limits, or configuration drifts are detected.
