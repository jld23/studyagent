"""Official Google Cloud PCA Case Studies Dossier.

Contains the comprehensive architectural profiles, business goals, technical
requirements, existing infrastructure, and GCP target architectures for the 4
official case studies tested on the Professional Cloud Architect exam:
1. Mountkirk Games
2. TerramEarth
3. EHR Healthcare
4. Helicopter Racing League (HRL)
"""

from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel


class CaseStudy(BaseModel):
    """Case study scenario for PCA exam."""

    id: str
    name: str
    company_overview: str
    business_requirements: List[str]
    technical_requirements: List[str]
    existing_environment: str
    recommended_gcp_architecture: Dict[str, str]
    architectural_tradeoffs: List[str]


PCA_CASE_STUDIES: Dict[str, CaseStudy] = {
    "mountkirk_games": CaseStudy(
        id="mountkirk_games",
        name="Mountkirk Games",
        company_overview="Mountkirk Games makes online, session-based multiplayer games for mobile platforms. They plan to release a new retro-style multiplayer game with millions of concurrent global users.",
        business_requirements=[
            "Support rapid global growth and unpredictable demand spikes without downtime.",
            "Minimize latency for players connecting globally.",
            "Optimize infrastructure operational costs and automate server management.",
            "Process game telemetry and player analytics in real time to adapt game mechanics.",
        ],
        technical_requirements=[
            "Dynamically scale backend game servers based on connected player count.",
            "Deploy multi-region backend services with global load balancing.",
            "Store transactional user profiles and game state in a globally consistent relational database.",
            "Ingest high-throughput telemetry data (100k+ events/sec) for real-time and historical analytics.",
        ],
        existing_environment="MySQL and Linux VMs deployed in a single on-premises datacenter with fixed capacity and manual deployment scripts.",
        recommended_gcp_architecture={
            "compute": "Google Kubernetes Engine (GKE) with Agones game server scaling or Autopilot across multiple regions.",
            "database": "Cloud Spanner for global transactional consistency and ACID compliance for player accounts.",
            "telemetry_ingestion": "Cloud Pub/Sub for high-throughput buffering, Cloud Dataflow for streaming ETL processing.",
            "analytics_storage": "BigQuery for real-time SQL analytics and Looker Studio for dashboards.",
            "networking": "Global External HTTPS / SSL Proxy Load Balancing with Cloud Armor DDoS mitigation.",
        },
        architectural_tradeoffs=[
            "Cloud Spanner chosen over Cloud SQL because Spanner provides global multi-region write consistency without manual sharding.",
            "GKE with Agones chosen over Compute Engine MIGs for millisecond-level container provisioning and UDP session state persistence.",
        ],
    ),
    "terramearth": CaseStudy(
        id="terramearth",
        name="TerramEarth",
        company_overview="TerramEarth manufactures heavy agricultural and mining equipment. 20 million connected vehicles worldwide collect real-time sensor metrics (engine temperature, vibration, fuel) to predict equipment failures.",
        business_requirements=[
            "Prevent costly machine downtime via proactive predictive maintenance.",
            "Ingest sensor data from 20M vehicles (5M connected via cellular, 15M uploading batch via dealer Wi-Fi).",
            "Enable third-party partners and dealers to access analytics APIs securely.",
            "Reduce data processing cost while maintaining multi-petabyte historical logs.",
        ],
        technical_requirements=[
            "Stream real-time telemetry from 5 million cellular-connected machines.",
            "Ingest large batch FTP/CSV uploads from 15 million machines at dealer service centers.",
            "Process petabytes of unstructured and structured time-series sensor data.",
            "Train machine learning models on historical failure data to predict maintenance windows.",
        ],
        existing_environment="Legacy web servers writing CSV files to on-prem SAN storage; nightly batch ETL jobs taking over 20 hours to complete.",
        recommended_gcp_architecture={
            "batch_ingestion": "Cloud Storage multi-region buckets for dealer Wi-Fi batch uploads; Storage Transfer Service / Transfer Appliance.",
            "streaming_ingestion": "Cloud Pub/Sub endpoint for cellular IoT telemetry.",
            "data_pipeline": "Cloud Dataflow (Apache Beam) to process both streaming and batch data into unified schemas.",
            "data_warehouse": "BigQuery partitioned and clustered by date and vehicle_id for fast ML feature generation.",
            "api_management": "Apigee API Management for secure external dealer and partner access with OAuth2 and rate limiting.",
            "machine_learning": "Vertex AI for training and deploying predictive maintenance failure models.",
        },
        architectural_tradeoffs=[
            "Cloud Pub/Sub + Dataflow chosen over Kafka to eliminate cluster management overhead and auto-scale dynamically.",
            "BigQuery table partitioning by Date and clustering by Vehicle ID minimizes query costs across 20M vehicles.",
        ],
    ),
    "ehr_healthcare": CaseStudy(
        id="ehr_healthcare",
        name="EHR Healthcare",
        company_overview="EHR Healthcare is a leading provider of Electronic Health Record software. They are migrating multiple on-premises hospital environments to Google Cloud to meet stringent HIPAA and patient privacy mandates.",
        business_requirements=[
            "Maintain 99.99% availability for clinical systems and emergency hospital operations.",
            "Comply with HIPAA regulations, data residency rules, and strict audit logging.",
            "Provide zero-downtime database migration from on-premises to Google Cloud.",
            "Enable secure multi-tenant isolation across different hospital client systems.",
        ],
        technical_requirements=[
            "Establish dedicated, private hybrid network connectivity between hospitals and GCP without traversing public Internet.",
            "Encrypt all patient data at rest using Customer-Managed Encryption Keys (CMEK) and rotate keys automatically.",
            "Implement VPC Service Controls to prevent unauthorized data exfiltration.",
            "Continuous automated deployment of microservices with binary authorization.",
        ],
        existing_environment="Colocated datacenters running VMware vSphere, Oracle RAC databases, and Microsoft Active Directory.",
        recommended_gcp_architecture={
            "hybrid_connectivity": "Dedicated Interconnect with Cloud VPN backup across redundant enterprise locations.",
            "identity_access": "Cloud Identity integrated with Active Directory using Google Cloud Directory Sync (GCDS); Cloud IAM with least privilege.",
            "security_encryption": "Cloud KMS with Customer-Managed Encryption Keys (CMEK) and automatic key rotation; Cloud DLP for de-identifying PII.",
            "network_security": "VPC Service Controls service perimeters around BigQuery, Cloud Storage, and Cloud SQL.",
            "compute_platform": "GKE Private Clusters with Anthos / GKE Enterprise and Binary Authorization.",
            "database_platform": "Cloud SQL for PostgreSQL (HA) or Bare Metal Solution for legacy Oracle workloads; Database Migration Service (DMS).",
        },
        architectural_tradeoffs=[
            "Dedicated Interconnect chosen over standard VPN due to high throughput (10+ Gbps) and SLA requirements for life-critical clinical operations.",
            "VPC Service Controls perimeters chosen to enforce data boundaries and eliminate egress risks even from compromised credentials.",
        ],
    ),
    "helicopter_racing_league": CaseStudy(
        id="helicopter_racing_league",
        name="Helicopter Racing League (HRL)",
        company_overview="HRL is a global sports league streaming live high-definition video of helicopter races. They want to enhance fan engagement with real-time telemetry overlays, AI predictive racing statistics, and global low-latency streaming.",
        business_requirements=[
            "Deliver low-latency live video streaming to millions of global viewers.",
            "Automatically tag video highlights and detect race telemetry events using AI/ML.",
            "Scale compute and network capacity dynamically during live 3-hour race events and scale to zero between events.",
            "Monetize historical race video archive through subscription tiers.",
        ],
        technical_requirements=[
            "Global content caching for video segments to reduce origin server load.",
            "Real-time video processing pipeline to transcode raw video feeds into multiple bitrates.",
            "Serverless event-driven processing to analyze race sensor telemetry and update live viewer leaderboards.",
            "Multi-region storage for archival video footage with lifecycle policies.",
        ],
        existing_environment="Third-party CDN provider and monolithic virtual machines hosted in a single regional cloud provider, suffering frequent buffering during peak races.",
        recommended_gcp_architecture={
            "video_ingestion_storage": "Cloud Storage Dual-Region / Multi-Region buckets; Transcoder API for multi-bitrate HLS/DASH encoding.",
            "cdn_distribution": "Cloud CDN integrated with Global External Application Load Balancer and Cloud Armor.",
            "realtime_telemetry": "Cloud Pub/Sub and Cloud Run / Cloud Functions for serverless event-driven leaderboard updates.",
            "ai_video_intelligence": "Vertex AI Video Intelligence API for automated highlight detection and object tracking.",
            "database": "Cloud Firestore for real-time mobile app leaderboard synchronization.",
        },
        architectural_tradeoffs=[
            "Cloud CDN + Cloud Storage origin chosen over single-origin VMs to cache 95%+ of video traffic at Google's global edge points of presence.",
            "Cloud Run serverless containers chosen over persistent VMs so compute automatically scales to zero when races end, reducing cost by 80%.",
        ],
    ),
}
