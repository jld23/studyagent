"""Official Google Cloud Professional Cloud Architect (PCA) Exam Domains & Objectives.

Contains the 6 canonical domains, sub-sections, core architectural principles,
and Google Cloud service mappings representing the official syllabus.
"""

from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel, Field


class SubObjective(BaseModel):
    """Sub-objective within a certification domain."""

    code: str
    title: str
    description: str
    key_services: List[str]


class ExamDomain(BaseModel):
    """Top-level certification domain."""

    domain_id: str
    domain_number: int
    title: str
    weight_percentage: int
    description: str
    sub_objectives: List[SubObjective]


PCA_DOMAINS: Dict[str, ExamDomain] = {
    "domain_1": ExamDomain(
        domain_id="domain_1",
        domain_number=1,
        title="Designing and planning a cloud solution architecture",
        weight_percentage=24,
        description="Design solution architectures meeting business and technical requirements, high availability, disaster recovery, compute/storage/network selection, and migration strategies.",
        sub_objectives=[
            SubObjective(
                code="1.1",
                title="Designing a solution infrastructure that meets business requirements",
                description="Business use case translation, financial planning, ROI, TCO, disaster recovery (RPO/RTO), high availability across zones/regions.",
                key_services=["Compute Engine", "GKE", "Cloud Run", "Cloud Storage", "Cloud Spanner", "Cloud SQL"],
            ),
            SubObjective(
                code="1.2",
                title="Designing a solution infrastructure that meets technical requirements",
                description="High performance, reliability, network latency, hybrid connectivity, compute scalability.",
                key_services=["Cloud Interconnect", "Cloud VPN", "VPC", "Cloud Load Balancing", "Cloud CDN"],
            ),
            SubObjective(
                code="1.3",
                title="Designing network, storage, and compute resources",
                description="Selecting storage products (Spanner vs Bigtable vs SQL vs BigQuery vs Firestore vs Cloud Storage), compute choices (GCE, GKE, Cloud Run), and networking topologies.",
                key_services=["Cloud Spanner", "Bigtable", "BigQuery", "Filestore", "Persistent Disk", "GKE Autopilot"],
            ),
            SubObjective(
                code="1.4",
                title="Creating a migration plan",
                description="Data and VM migration strategies, Database Migration Service, Storage Transfer Service, Transfer Appliance, Migrate for Compute Engine/Containers.",
                key_services=["Database Migration Service", "Storage Transfer Service", "Migrate to Containers", "Transfer Appliance"],
            ),
        ],
    ),
    "domain_2": ExamDomain(
        domain_id="domain_2",
        domain_number=2,
        title="Managing and provisioning a solution infrastructure",
        weight_percentage=18,
        description="Provision and configure VPC networks, hybrid connectivity, storage policies, and compute workloads.",
        sub_objectives=[
            SubObjective(
                code="2.1",
                title="Configuring network topologies",
                description="Shared VPC, VPC Network Peering, Cloud Router, Private Service Connect (PSC), Cloud NAT, Firewall Rules, Cloud DNS.",
                key_services=["Shared VPC", "VPC Peering", "Private Service Connect", "Cloud NAT", "Cloud Router"],
            ),
            SubObjective(
                code="2.2",
                title="Configuring individual storage systems",
                description="Cloud Storage lifecycle rules, retention policies, bucket locks, Cloud SQL HA and read replicas, Spanner multi-region instance configs, Bigtable app profiles.",
                key_services=["Cloud Storage", "Cloud SQL", "Cloud Spanner", "Cloud Bigtable", "Memorystore"],
            ),
            SubObjective(
                code="2.3",
                title="Configuring compute systems",
                description="GKE cluster configuration, Node Auto-Provisioning, Workload Identity, Compute Engine Managed Instance Groups (MIGs), Cloud Run jobs.",
                key_services=["GKE", "Compute Engine MIGs", "Cloud Run", "Artifact Registry"],
            ),
        ],
    ),
    "domain_3": ExamDomain(
        domain_id="domain_3",
        domain_number=3,
        title="Designing for security and compliance",
        weight_percentage=18,
        description="IAM least privilege, service accounts, encryption (CMEK/CSEK/KMS), VPC Service Controls, Cloud Armor, Security Command Center, and compliance.",
        sub_objectives=[
            SubObjective(
                code="3.1",
                title="Designing for security",
                description="IAM roles and conditions, Workload Identity Federation, Service Account Key minimization, Secret Manager, Cloud KMS CMEK, Cloud Armor DDoS/WAF protection.",
                key_services=["Cloud IAM", "Workload Identity", "Cloud KMS", "Secret Manager", "Cloud Armor", "VPC Service Controls"],
            ),
            SubObjective(
                code="3.2",
                title="Designing for compliance",
                description="Data residency and sovereignty, HIPAA/GDPR compliance, Cloud DLP for PII masking, Cloud Audit Logs, Security Command Center (SCC).",
                key_services=["Cloud DLP", "Security Command Center", "Cloud Audit Logs", "Access Transparency"],
            ),
        ],
    ),
    "domain_4": ExamDomain(
        domain_id="domain_4",
        domain_number=4,
        title="Analyzing and optimizing technical and business processes",
        weight_percentage=14,
        description="CI/CD automation, testing methodologies, multi-environment release strategies, cost optimization, and capacity planning.",
        sub_objectives=[
            SubObjective(
                code="4.1",
                title="Analyzing and optimizing technical processes",
                description="CI/CD pipelines with Cloud Build and Cloud Deploy, canary/blue-green deployments, container image vulnerability scanning.",
                key_services=["Cloud Build", "Cloud Deploy", "Artifact Registry", "Binary Authorization"],
            ),
            SubObjective(
                code="4.2",
                title="Analyzing and optimizing business processes",
                description="Cost management, Committed Use Discounts (CUDs), billing export to BigQuery, budget alerts, SRE operational workflows.",
                key_services=["Cloud Billing", "BigQuery Billing Export", "Cost Table", "Recommender"],
            ),
        ],
    ),
    "domain_5": ExamDomain(
        domain_id="domain_5",
        domain_number=5,
        title="Managing implementation",
        weight_percentage=12,
        description="Advising engineering teams on GCP best practices, Infrastructure as Code (Terraform), and programmatic API/SDK interactions.",
        sub_objectives=[
            SubObjective(
                code="5.1",
                title="Advising development and operations teams",
                description="Application modernization, 12-factor cloud-native principles, API design with Apigee, event-driven architectures with Eventarc and Pub/Sub.",
                key_services=["Pub/Sub", "Eventarc", "Apigee", "Cloud Tasks", "Cloud Workflows"],
            ),
            SubObjective(
                code="5.2",
                title="Interacting with Google Cloud programmatically",
                description="Google Cloud SDK (gcloud), Terraform Google Provider, Cloud Client Libraries, REST APIs.",
                key_services=["Terraform", "Google Cloud SDK", "Cloud Client Libraries"],
            ),
        ],
    ),
    "domain_6": ExamDomain(
        domain_id="domain_6",
        domain_number=6,
        title="Ensuring solution and operations reliability",
        weight_percentage=14,
        description="Monitoring, alerting, log aggregation, distributed tracing, incident postmortems, SLI/SLO/SLA management, and chaos testing.",
        sub_objectives=[
            SubObjective(
                code="6.1",
                title="Monitoring, logging, and alerting",
                description="Cloud Monitoring dashboards, alert policies, log-based metrics, Cloud Logging export/sinks, Cloud Trace, Cloud Profiler.",
                key_services=["Cloud Monitoring", "Cloud Logging", "Cloud Trace", "Cloud Profiler", "Error Reporting"],
            ),
            SubObjective(
                code="6.2",
                title="Troubleshooting and support",
                description="Network Intelligence Center, Connectivity Tests, packet mirroring, post-incident analysis, defining SLIs, SLOs, and Error Budgets.",
                key_services=["Network Intelligence Center", "Cloud Support API", "Cloud Monitoring SLOs"],
            ),
        ],
    ),
}
