"""Comprehensive Question & Flashcard Bank for PCA Exam Preparation.

Includes scenario-based questions with distractor analysis across all 6 domains
and 4 case studies, plus architectural flashcards for spaced repetition drills.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class QuestionOption(BaseModel):
    """Multiple choice option."""

    key: str  # 'A', 'B', 'C', 'D'
    text: str


class ExamQuestion(BaseModel):
    """Scenario-based PCA exam question."""

    id: str
    domain_id: str
    sub_objective_code: str
    difficulty: str = Field(description="'beginner', 'intermediate', 'expert'")
    case_study_id: Optional[str] = None
    question_text: str
    options: List[QuestionOption]
    correct_option: str
    architectural_principle: str
    explanation: str
    distractor_analysis: Dict[str, str]


class Flashcard(BaseModel):
    """Architectural decision flashcard for spaced repetition."""

    id: str
    domain_id: str
    topic: str
    front_prompt: str
    back_solution: str
    key_tradeoff: str


PCA_QUESTIONS: List[ExamQuestion] = [
    # -------------------------------------------------------------------------
    # DOMAIN 1: Designing and Planning a Cloud Solution Architecture
    # -------------------------------------------------------------------------
    ExamQuestion(
        id="q_pca_001",
        domain_id="domain_1",
        sub_objective_code="1.3",
        difficulty="expert",
        case_study_id="mountkirk_games",
        question_text=(
            "Mountkirk Games is releasing a new global multiplayer game with millions of concurrent users. "
            "They require a relational database that provides ACID transactions, global multi-region scalability, "
            "and sub-10ms read latency with zero downtime maintenance. Which Google Cloud database should you recommend?"
        ),
        options=[
            QuestionOption(key="A", text="Cloud SQL for MySQL configured with cross-region read replicas and automated failover."),
            QuestionOption(key="B", text="Cloud Spanner configured with a multi-region instance configuration."),
            QuestionOption(key="C", text="Cloud Bigtable with a multi-cluster routing configuration."),
            QuestionOption(key="D", text="Firestore in Datastore mode configured with a multi-region location."),
        ],
        correct_option="B",
        architectural_principle="Global Multi-Region Relational ACID Consistency",
        explanation=(
            "Cloud Spanner is Google Cloud's fully managed, globally distributed, horizontally scalable SQL database "
            "that provides ACID transactions, 99.999% availability for multi-region configurations, and synchronous replication "
            "using TrueTime."
        ),
        distractor_analysis={
            "A": "Cloud SQL cross-region replicas are asynchronous and do not support multi-region write scalability or global ACID transactions.",
            "C": "Cloud Bigtable is a wide-column NoSQL database suitable for high-throughput time-series, not relational ACID transactions.",
            "D": "Firestore is a NoSQL document database, not a relational database with SQL schemas and multi-table ACID transactions.",
        },
    ),
    ExamQuestion(
        id="q_pca_007",
        domain_id="domain_1",
        sub_objective_code="1.1",
        difficulty="expert",
        case_study_id="helicopter_racing_league",
        question_text=(
            "Helicopter Racing League (HRL) needs to serve low-latency live video telemetry and predictive telemetry streams "
            "to millions of global viewers during live race broadcasts. The system must automatically scale from zero to millions "
            "of viewers within minutes and minimize egress bandwidth costs. Which architecture best satisfies these requirements?"
        ),
        options=[
            QuestionOption(key="A", text="Deploy Compute Engine Managed Instance Groups behind internal TCP load balancers in every race city."),
            QuestionOption(key="B", text="Use Cloud CDN in front of a Global External Application Load Balancer with Cloud Run backend microservices."),
            QuestionOption(key="C", text="Ingest video directly to Cloud Storage buckets with public read ACLs without load balancers."),
            QuestionOption(key="D", text="Stream telemetry to Google Kubernetes Engine (GKE) clusters using NodePort services."),
        ],
        correct_option="B",
        architectural_principle="Global Edge Caching and Serverless Auto-Scaling",
        explanation=(
            "Cloud CDN caches video segments and telemetry at Google's global points of presence (Edge PoPs), drastically "
            "reducing latency and origin egress costs. Cloud Run handles rapid zero-to-millions autoscaling seamlessly."
        ),
        distractor_analysis={
            "A": "Internal TCP Load Balancers cannot serve public internet viewers globally and lack edge caching.",
            "C": "Direct Cloud Storage public access lacks global anycast routing, caching optimizations, and backend compute filtering.",
            "D": "GKE NodePort exposes raw cluster ports rather than global edge anycast IP load balancing and CDN caching.",
        },
    ),
    ExamQuestion(
        id="q_pca_008",
        domain_id="domain_1",
        sub_objective_code="1.2",
        difficulty="intermediate",
        case_study_id="terramearth",
        question_text=(
            "TerramEarth has 20 million agricultural vehicles worldwide that collect sensor data intermittently. "
            "Vehicles in remote regions store 500 MB of diagnostic data daily and upload it via cellular or dealership Wi-Fi. "
            "You need to design a cost-effective ingestion storage tier that accommodates unpredictable batch uploads and minimizes storage costs. What should you recommend?"
        ),
        options=[
            QuestionOption(key="A", text="Upload raw files to Cloud Storage Standard class, with an Object Lifecycle Management rule transitioning data to Coldline after 30 days."),
            QuestionOption(key="B", text="Insert raw data directly into Cloud Spanner database tables using batch insert mutations."),
            QuestionOption(key="C", text="Store files on Filestore enterprise NFS instances mounted across multi-region VMs."),
            QuestionOption(key="D", text="Stream all batch uploads directly into BigQuery streaming buffer endpoints."),
        ],
        correct_option="A",
        architectural_principle="Tiered Object Storage with Automated Lifecycle Policies",
        explanation=(
            "Cloud Storage Standard provides scalable, low-latency object ingestion. Lifecycle policies automatically transition "
            "older diagnostic files to Coldline or Archive storage, dramatically reducing long-term storage costs without manual intervention."
        ),
        distractor_analysis={
            "B": "Cloud Spanner is designed for relational transactions, making it prohibitively expensive for multi-terabyte raw sensor file blobs.",
            "C": "Filestore Enterprise is an NFS file share designed for high-performance shared file systems, not global distributed batch uploads.",
            "D": "BigQuery streaming insert incurs ingestion per-MB costs; batch loading from Cloud Storage is free and better suited for 500MB daily files.",
        },
    ),
    ExamQuestion(
        id="q_pca_009",
        domain_id="domain_1",
        sub_objective_code="1.4",
        difficulty="expert",
        case_study_id=None,
        question_text=(
            "An enterprise is designing a disaster recovery architecture with an RTO (Recovery Time Objective) of less than 15 minutes "
            "and an RPO (Recovery Point Objective) of near zero across two geographical regions. Which database and compute architecture satisfies these constraints?"
        ),
        options=[
            QuestionOption(key="A", text="Cloud SQL for PostgreSQL with cross-region asynchronous read replicas and manual VM promotion."),
            QuestionOption(key="B", text="Multi-Region Cloud Spanner with multi-region GKE clusters deployed behind a Global External Application Load Balancer."),
            QuestionOption(key="C", text="Compute Engine Managed Instance Groups taking daily snapshots replicated to a secondary region."),
            QuestionOption(key="D", text="Firestore with daily automated exports to Cloud Storage Archive in a secondary bucket."),
        ],
        correct_option="B",
        architectural_principle="Synchronous Multi-Region Replication for Zero-RPO Failover",
        explanation=(
            "Multi-Region Cloud Spanner provides synchronous replication across regions with sub-second RPO and automatic failover (zero RTO). "
            "Combined with Multi-Region GKE and Global Anycast Load Balancing, traffic is instantaneously rerouted to healthy regions."
        ),
        distractor_analysis={
            "A": "Asynchronous replication in Cloud SQL introduces data loss on primary failure (violates near-zero RPO) and requires manual promotion (violates 15-min RTO).",
            "C": "Daily snapshots create an RPO of up to 24 hours.",
            "D": "Daily database exports create up to 24 hours of data loss on recovery.",
        },
    ),

    # -------------------------------------------------------------------------
    # DOMAIN 2: Managing and Provisioning a Solution Infrastructure
    # -------------------------------------------------------------------------
    ExamQuestion(
        id="q_pca_002",
        domain_id="domain_2",
        sub_objective_code="2.1",
        difficulty="intermediate",
        case_study_id=None,
        question_text=(
            "An enterprise organization has 15 different GCP projects managed by different business units. "
            "They need all projects to share a unified private corporate IP space and access on-premises resources via "
            "a single Dedicated Interconnect, while maintaining strict separation of IAM roles for network administrators "
            "versus project developers. What architecture should you implement?"
        ),
        options=[
            QuestionOption(key="A", text="Create VPC Network Peering full-mesh connections between all 15 project VPCs."),
            QuestionOption(key="B", text="Configure a Shared VPC with a central Host Project and 15 Service Projects."),
            QuestionOption(key="C", text="Deploy Cloud VPN gateways in every single project connecting to on-premises routers."),
            QuestionOption(key="D", text="Use Private Service Connect endpoints in every project to expose each internal service."),
        ],
        correct_option="B",
        architectural_principle="Centralized Network Administration with Shared VPC",
        explanation=(
            "Shared VPC allows an organization to connect resources from multiple service projects to a common VPC network "
            "hosted in a central host project. Network administrators maintain centralized control over subnets, routes, and firewalls, "
            "while service project admins manage their own compute instances."
        ),
        distractor_analysis={
            "A": "VPC Network Peering does not scale cleanly to full mesh across many projects, is non-transitive, and creates administrative overhead.",
            "C": "Cloud VPN in every project multiplies cost, violates the single Dedicated Interconnect requirement, and increases administrative burden.",
            "D": "Private Service Connect is for service-to-service publishing, not unified private subnet sharing and on-prem hybrid routing.",
        },
    ),
    ExamQuestion(
        id="q_pca_010",
        domain_id="domain_2",
        sub_objective_code="2.2",
        difficulty="expert",
        case_study_id=None,
        question_text=(
            "You need to establish high-availability, low-latency hybrid connectivity between your on-premises data center "
            "and Google Cloud with a 99.99% availability SLA. Which network architecture is required by Google Cloud to achieve this SLA?"
        ),
        options=[
            QuestionOption(key="A", text="Deploy two Dedicated Interconnect connections to the same Google Colocation facility (Metropolitan Area) using a single Cloud Router."),
            QuestionOption(key="B", text="Deploy at least four Dedicated Interconnect connections across two different Google Colocation facilities (Edge PoPs) and two distinct Cloud Routers in two different GCP regions."),
            QuestionOption(key="C", text="Deploy a single Dedicated Interconnect connection and an IPsec Cloud VPN backup tunnel."),
            QuestionOption(key="D", text="Deploy HA VPN over the public internet with dual-peer gateways."),
        ],
        correct_option="B",
        architectural_principle="99.99% Production Hybrid Connectivity SLA Architecture",
        explanation=(
            "To achieve Google Cloud's 99.99% SLA for Dedicated Interconnect, you must provision 4 interconnect circuits across "
            "2 distinct metropolitan colocation facilities (2 circuits per metro) terminating on 2 Cloud Routers in different regions."
        ),
        distractor_analysis={
            "A": "A single metro facility and single Cloud Router provides only 99.9% SLA (vulnerable to facility-wide power or fiber cuts).",
            "C": "Interconnect with VPN backup does not meet the 99.99% Dedicated Interconnect SLA guidelines and throttles bandwidth during failover.",
            "D": "HA VPN over public internet provides a 99.99% SLA for VPN tunnels, but is subject to public internet transit latency variations.",
        },
    ),
    ExamQuestion(
        id="q_pca_011",
        domain_id="domain_2",
        sub_objective_code="2.3",
        difficulty="intermediate",
        case_study_id=None,
        question_text=(
            "Your company runs containerized batch workloads on GKE that can tolerate unexpected node preemptions "
            "and must run at the lowest possible infrastructure cost. How should you configure your GKE cluster node pools?"
        ),
        options=[
            QuestionOption(key="A", text="Create a node pool configured with Spot VMs, GKE cluster autoscaler, and Kubernetes Pod Disruption Budgets."),
            QuestionOption(key="B", text="Use dedicated Compute Engine sole-tenant nodes with committed use discounts."),
            QuestionOption(key="C", text="Configure default standard node pools with persistent local SSD disks."),
            QuestionOption(key="D", text="Deploy a single large custom VM node with overprovisioned CPU cores."),
        ],
        correct_option="A",
        architectural_principle="Cost Optimization via Spot VMs and Cluster Autoscaling",
        explanation=(
            "Spot VMs offer up to 60-91% discounts compared to standard VMs for fault-tolerant, stateless batch workloads. "
            "GKE automatically provisions and replaces preempted Spot instances with cluster autoscaler."
        ),
        distractor_analysis={
            "B": "Sole-tenant nodes are intended for licensing, regulatory compliance, and hardware isolation, carrying premium costs.",
            "C": "Standard VMs with local SSDs are expensive and not optimized for interruptible batch workloads.",
            "D": "A single large VM represents a single point of failure and cannot dynamically scale down to zero.",
        },
    ),

    # -------------------------------------------------------------------------
    # DOMAIN 3: Designing for Security and Compliance
    # -------------------------------------------------------------------------
    ExamQuestion(
        id="q_pca_003",
        domain_id="domain_3",
        sub_objective_code="3.1",
        difficulty="expert",
        case_study_id="ehr_healthcare",
        question_text=(
            "EHR Healthcare must comply with strict HIPAA regulations and prevent data exfiltration. "
            "Even if a developer's authorized service account credentials are compromised, data in Cloud Storage buckets "
            "and BigQuery datasets must not be downloadable from unauthorized networks or outside IP addresses. What should you configure?"
        ),
        options=[
            QuestionOption(key="A", text="Apply Cloud IAM Deny policies to all developer service accounts after work hours."),
            QuestionOption(key="B", text="Implement VPC Service Controls to define a security perimeter around Cloud Storage and BigQuery."),
            QuestionOption(key="C", text="Enable Customer-Supplied Encryption Keys (CSEK) on all Cloud Storage objects."),
            QuestionOption(key="D", text="Deploy Cloud Armor security policies on the backend storage buckets."),
        ],
        correct_option="B",
        architectural_principle="VPC Service Controls Data Perimeter Defense",
        explanation=(
            "VPC Service Controls allows organizations to define fine-grained perimeter security around Google Cloud services "
            "like Cloud Storage and BigQuery. It blocks unauthorized data ingress and egress even if authorized credentials are used "
            "from an untrusted location or network."
        ),
        distractor_analysis={
            "A": "Time-based IAM deny policies do not prevent data exfiltration during active hours and do not restrict network context.",
            "C": "CSEK encrypts data at rest, but authorized credentials can still decrypt and exfiltrate data from unauthorized networks.",
            "D": "Cloud Armor protects HTTP(S) Load Balancers and Cloud Run/GKE backends, not direct API access to Cloud Storage or BigQuery.",
        },
    ),
    ExamQuestion(
        id="q_pca_012",
        domain_id="domain_3",
        sub_objective_code="3.2",
        difficulty="intermediate",
        case_study_id=None,
        question_text=(
            "You need to allow external auditors to inspect financial analytics in BigQuery. The datasets contain columns with "
            "Personally Identifiable Information (PII) such as Social Security Numbers and credit card numbers. Auditors should "
            "be able to query statistical aggregates but must never view unmasked PII data. What should you configure?"
        ),
        options=[
            QuestionOption(key="A", text="Create separate sanitized BigQuery tables by exporting data daily to CSV files."),
            QuestionOption(key="B", text="Implement BigQuery Policy Tags with Column-Level Access Control and Dynamic Data Masking rules."),
            QuestionOption(key="C", text="Assign the BigQuery Data Viewer role to auditors and enforce IAM Conditions on row timestamps."),
            QuestionOption(key="D", text="Encrypt the PII columns using client-side symmetric keys before writing to BigQuery."),
        ],
        correct_option="B",
        architectural_principle="Fine-Grained Column-Level Security & Dynamic Masking",
        explanation=(
            "BigQuery Column-Level Access Control uses Data Catalog Policy Tags to restrict access to specific sensitive columns. "
            "Dynamic Data Masking automatically transforms column values (e.g. SHA256 hashing or partial masking) for unauthorized roles in real time."
        ),
        distractor_analysis={
            "A": "Exporting duplicate CSV tables introduces synchronization delay, data duplication, and maintenance overhead.",
            "C": "BigQuery Data Viewer grants read access to all columns within the dataset table.",
            "D": "Client-side encryption prevents BigQuery from executing native SQL analytical queries and aggregates on those columns.",
        },
    ),
    ExamQuestion(
        id="q_pca_013",
        domain_id="domain_3",
        sub_objective_code="3.3",
        difficulty="expert",
        case_study_id="mountkirk_games",
        question_text=(
            "Mountkirk Games is deploying public gaming API backends on GKE and needs to protect against Layer 7 DDoS attacks, "
            "SQL injection, and cross-site scripting (XSS) at the network perimeter before traffic reaches the application pods. "
            "Which Google Cloud solution should you implement?"
        ),
        options=[
            QuestionOption(key="A", text="Configure Cloud Armor security policies with preconfigured WAF rules attached to an External Application Load Balancer."),
            QuestionOption(key="B", text="Deploy iptables firewall rules on each Kubernetes worker node."),
            QuestionOption(key="C", text="Use Cloud NAT gateway filtering with IP allowlists."),
            QuestionOption(key="D", text="Enable Google Cloud IDS (Intrusion Detection System) on the VPC subnet."),
        ],
        correct_option="A",
        architectural_principle="Edge Web Application Firewall (WAF) & DDoS Defense",
        explanation=(
            "Google Cloud Armor provides enterprise DDoS mitigation and Web Application Firewall (WAF) filtering directly at Google's "
            "global edge infrastructure, inspecting HTTP/HTTPS requests against OWASP Top 10 vulnerabilities before reaching GKE backends."
        ),
        distractor_analysis={
            "B": "Node iptables operate at Layer 3/4 and cannot perform deep Layer 7 HTTP payload inspection or manage global DDoS attacks.",
            "C": "Cloud NAT is for outbound internet access from private instances, not inbound DDoS and WAF protection.",
            "D": "Cloud IDS detects and alerts on threats via traffic mirroring, but does not perform active inline blocking of incoming Layer 7 attacks.",
        },
    ),

    # -------------------------------------------------------------------------
    # DOMAIN 4: Analyzing and Optimizing Technical and Business Processes
    # -------------------------------------------------------------------------
    ExamQuestion(
        id="q_pca_004",
        domain_id="domain_4",
        sub_objective_code="4.1",
        difficulty="intermediate",
        case_study_id=None,
        question_text=(
            "Your company is adopting a Continuous Delivery strategy on GKE. You want to automate progressive deployments "
            "so that new releases are first deployed to a canary target (10% traffic), tested, and automatically rolled back "
            "if error rates increase, before advancing to staging and production. Which native Google Cloud service is designed for this?"
        ),
        options=[
            QuestionOption(key="A", text="Cloud Deploy with multi-target delivery pipelines and automated canary progression."),
            QuestionOption(key="B", text="Cloud Build running custom bash deployment scripts in parallel."),
            QuestionOption(key="C", text="Compute Engine Managed Instance Group auto-healing policies."),
            QuestionOption(key="D", text="Cloud Scheduler triggering Cloud Functions to update Kubernetes deployment manifests."),
        ],
        correct_option="A",
        architectural_principle="Continuous Delivery & Progressive Rollouts with Cloud Deploy",
        explanation=(
            "Google Cloud Deploy is a managed, opinionated continuous delivery service for GKE, Cloud Run, and Anthos. "
            "It provides native support for pipeline stages, progressive delivery (canaries), approvals, and one-click/automated rollbacks."
        ),
        distractor_analysis={
            "B": "Cloud Build is a continuous integration tool for building and testing artifacts, but lacks native multi-target release pipelines and approval gating.",
            "C": "MIG auto-healing is for VM instance health replacement, not GKE application progressive canary delivery.",
            "D": "Custom Cloud Functions create high maintenance overhead and lack declarative delivery pipeline observability.",
        },
    ),
    ExamQuestion(
        id="q_pca_014",
        domain_id="domain_4",
        sub_objective_code="4.2",
        difficulty="intermediate",
        case_study_id=None,
        question_text=(
            "You need to migrate an on-premises Oracle database (5 TB) to Google Cloud with minimal application downtime. "
            "The target architecture must modernize into an open-source relational database. Which migration path should you select?"
        ),
        options=[
            QuestionOption(key="A", text="Take an Oracle RMAN database dump, upload to Cloud Storage, and restore to Cloud Spanner."),
            QuestionOption(key="B", text="Use Database Migration Service (DMS) with continuous Change Data Capture (CDC) to migrate and replicate data to Cloud SQL for PostgreSQL."),
            QuestionOption(key="C", text="Deploy an Oracle database on Compute Engine VMs and configure cross-cloud database mirroring."),
            QuestionOption(key="D", text="Export tables to Avro files and stream into BigQuery via Dataflow."),
        ],
        correct_option="B",
        architectural_principle="Heterogeneous Database Modernization with Minimal Downtime",
        explanation=(
            "Google Cloud Database Migration Service (DMS) supports homogeneous and heterogeneous migrations. For Oracle to PostgreSQL, "
            "it performs schema translation and initial data loading followed by continuous CDC replication, enabling near-zero downtime cutovers."
        ),
        distractor_analysis={
            "A": "Oracle RMAN dumps are proprietary and cannot be restored directly into Cloud Spanner schemas.",
            "C": "Running Oracle on Compute Engine retains proprietary licensing costs and does not modernize to open-source managed services.",
            "D": "BigQuery is an analytical data warehouse, not an OLTP database for application transactions.",
        },
    ),
    ExamQuestion(
        id="q_pca_015",
        domain_id="domain_4",
        sub_objective_code="4.3",
        difficulty="expert",
        case_study_id=None,
        question_text=(
            "Your company has a hybrid cloud architecture. Development teams frequently provision unapproved compute resources "
            "in non-compliant geographical regions. As the Principal Architect, you need to enforce strict organizational guardrails "
            "so that resources can only be created in specific approved Google Cloud regions across all projects. What should you configure?"
        ),
        options=[
            QuestionOption(key="A", text="Write a Cloud Function that runs hourly to scan all projects and terminate out-of-region VMs."),
            QuestionOption(key="B", text="Define an Organization Policy with the Resource Location Restriction constraint applied at the organization root."),
            QuestionOption(key="C", text="Revoke the Compute Admin role from all developers and require manual approval for all VM creations."),
            QuestionOption(key="D", text="Configure IAM Conditions on every developer role in every project."),
        ],
        correct_option="B",
        architectural_principle="Centralized Governance via Organization Policies",
        explanation=(
            "Organization Policies provide centralized, declarative governance across the entire resource hierarchy. The `gcp.resourceLocations` "
            "constraint enforces location compliance preventatively at creation time, blocking deployments in unapproved regions."
        ),
        distractor_analysis={
            "A": "Reactive Cloud Functions only detect violations after resources have already been deployed and incur costs.",
            "C": "Manual ticketing bottlenecks velocity and does not scale across enterprise teams.",
            "D": "Managing individual IAM conditions across dozens of projects creates severe drift and administrative burden.",
        },
    ),

    # -------------------------------------------------------------------------
    # DOMAIN 5: Managing Implementation of Cloud Architecture
    # -------------------------------------------------------------------------
    ExamQuestion(
        id="q_pca_005",
        domain_id="domain_5",
        sub_objective_code="5.1",
        difficulty="intermediate",
        case_study_id="terramearth",
        question_text=(
            "TerramEarth needs to ingest real-time telematics from 5 million connected vehicles with minimal latency "
            "and buffer unpredictable spikes of millions of events per second without dropping messages. "
            "Which architecture should you recommend?"
        ),
        options=[
            QuestionOption(key="A", text="Ingest sensor metrics directly into Cloud SQL using JDBC connection pooling."),
            QuestionOption(key="B", text="Publish sensor messages to Cloud Pub/Sub, then consume and process with Cloud Dataflow into BigQuery."),
            QuestionOption(key="C", text="Write sensor payloads to local SSD on Compute Engine VMs and run daily rsync jobs."),
            QuestionOption(key="D", text="Post sensor metrics directly to Cloud Bigtable via standard HTTP REST endpoints from vehicles."),
        ],
        correct_option="B",
        architectural_principle="Decoupled Scalable Event Streaming Architecture",
        explanation=(
            "Cloud Pub/Sub provides scalable, highly available asynchronous messaging capable of ingesting millions of events per second. "
            "Cloud Dataflow provides autoscaling stream processing to transform data and load it into BigQuery for analysis."
        ),
        distractor_analysis={
            "A": "Cloud SQL will be overwhelmed by millions of concurrent write connections and lacks buffer elasticity.",
            "C": "Local SSD with batch rsync introduces multi-hour latency and severe risk of data loss on VM termination.",
            "D": "Vehicles posting directly to Bigtable creates connection scalability issues and lacks a durable streaming buffer.",
        },
    ),
    ExamQuestion(
        id="q_pca_016",
        domain_id="domain_5",
        sub_objective_code="5.2",
        difficulty="expert",
        case_study_id="terramearth",
        question_text=(
            "TerramEarth wants to run predictive maintenance ML models over vehicle sensor data to predict parts failures "
            "2 weeks in advance. The data science team needs to train models using petabytes of structured historical telematics "
            "data stored in BigQuery without moving or exporting files. Which Google Cloud machine learning approach should you use?"
        ),
        options=[
            QuestionOption(key="A", text="Export BigQuery data to TFRecord files in Cloud Storage and train custom TensorFlow models on Compute Engine VMs with GPUs."),
            QuestionOption(key="B", text="Train machine learning models directly inside BigQuery using BigQuery ML (BQML)."),
            QuestionOption(key="C", text="Load data from BigQuery into a Cloud SQL instance and use Python scikit-learn scripts."),
            QuestionOption(key="D", text="Stream predictions via Cloud Functions querying Cloud Bigtable."),
        ],
        correct_option="B",
        architectural_principle="In-Database Machine Learning at Scale with BigQuery ML",
        explanation=(
            "BigQuery ML allows data scientists to train, evaluate, and operationalize ML models directly inside BigQuery using standard SQL. "
            "It eliminates data export latency, leverages BigQuery's massively parallel computing infrastructure, and handles petabyte datasets effortlessly."
        ),
        distractor_analysis={
            "A": "Exporting petabytes of data to Cloud Storage and managing manual GPU infrastructure creates high egress costs and infrastructure management overhead.",
            "C": "Cloud SQL cannot scale to petabyte datasets required for large-scale enterprise machine learning.",
            "D": "Cloud Functions querying Bigtable is for real-time serving, not training predictive models over historical petabyte datasets.",
        },
    ),
    ExamQuestion(
        id="q_pca_017",
        domain_id="domain_5",
        sub_objective_code="5.3",
        difficulty="intermediate",
        case_study_id="helicopter_racing_league",
        question_text=(
            "Helicopter Racing League (HRL) captures high-definition video from cameras on helicopters during races. "
            "They need to automatically detect team logos, transcribe pilot audio commentary, and identify racing incidents in real time. "
            "Which pre-trained Google Cloud AI services should they integrate?"
        ),
        options=[
            QuestionOption(key="A", text="Cloud Video Intelligence API for video label/logo detection and Speech-to-Text API for audio transcription."),
            QuestionOption(key="B", text="Train custom convolutional neural networks from scratch on Compute Engine VMs."),
            QuestionOption(key="C", text="Use Google Cloud Natural Language API for video stream pixel parsing."),
            QuestionOption(key="D", text="Deploy Apache OpenNLP on GKE clusters."),
        ],
        correct_option="A",
        architectural_principle="Turnkey Pre-Trained AI Services for Media Intelligence",
        explanation=(
            "Cloud Video Intelligence API automatically extracts video metadata, tracks objects, and recognizes logos. "
            "Speech-to-Text API provides real-time streaming audio transcription with high accuracy."
        ),
        distractor_analysis={
            "B": "Training models from scratch requires months of data labeling, high GPU expenses, and deep ML specialization.",
            "C": "Natural Language API parses text syntax and sentiment, not video stream pixels.",
            "D": "Self-managed OpenNLP requires heavy infrastructure maintenance and lacks multimodal video capabilities.",
        },
    ),

    # -------------------------------------------------------------------------
    # DOMAIN 6: Ensuring Solution and Operations Reliability
    # -------------------------------------------------------------------------
    ExamQuestion(
        id="q_pca_006",
        domain_id="domain_6",
        sub_objective_code="6.1",
        difficulty="intermediate",
        case_study_id=None,
        question_text=(
            "An e-commerce application on Cloud Run experiences intermittent 504 Gateway Timeout errors during high-traffic events. "
            "The development team needs to pinpoint which internal downstream microservice call is introducing high latency. "
            "Which Google Cloud observability tool should be enabled?"
        ),
        options=[
            QuestionOption(key="A", text="Cloud Monitoring Metric Explorer to inspect CPU utilization."),
            QuestionOption(key="B", text="Cloud Trace to capture distributed latency spans across microservices."),
            QuestionOption(key="C", text="Cloud Logging log-based alerts for HTTP 504 status codes."),
            QuestionOption(key="D", text="Error Reporting to group application stack traces."),
        ],
        correct_option="B",
        architectural_principle="Distributed Tracing for Latency Bottleneck Identification",
        explanation=(
            "Cloud Trace is a distributed tracing system that collects latency data from your applications and displays it in near real time. "
            "It tracks requests as they propagate through distributed microservices, highlighting the exact slow RPC calls."
        ),
        distractor_analysis={
            "A": "CPU metrics show aggregate resource consumption, not per-request latency across service boundaries.",
            "C": "Log-based alerts notify when 504 errors occur, but do not profile end-to-end downstream RPC request latencies.",
            "D": "Error Reporting aggregates uncaught application exceptions, but does not provide distributed RPC latency traces.",
        },
    ),
    ExamQuestion(
        id="q_pca_018",
        domain_id="domain_6",
        sub_objective_code="6.2",
        difficulty="expert",
        case_study_id=None,
        question_text=(
            "You are defining Site Reliability Engineering (SRE) Service Level Objectives (SLOs) for a critical banking API. "
            "The business requires 99.9% availability per calendar month. During the first two weeks of the month, unexpected outages "
            "consume 100% of the monthly error budget. According to Google SRE principles, what action should the team take for the remainder of the month?"
        ),
        options=[
            QuestionOption(key="A", text="Halt new feature releases and redirect engineering effort toward reliability, testing, and automation."),
            QuestionOption(key="B", text="Lower the SLO target to 99.0% so feature deployments can continue uninterrupted."),
            QuestionOption(key="C", text="Double the Compute Engine VM capacity to mask software bugs."),
            QuestionOption(key="D", text="Disable automated monitoring alerts to prevent alert fatigue."),
        ],
        correct_option="A",
        architectural_principle="SRE Error Budget Policy & Release Gating",
        explanation=(
            "In Google SRE practices, when an error budget is exhausted, product feature deployments are temporarily frozen. "
            "Engineering focus shifts entirely to post-mortem analysis, fixing underlying stability flaws, and improving monitoring."
        ),
        distractor_analysis={
            "B": "Lowering SLO targets undermines user trust and violates contractual reliability agreements.",
            "C": "Scaling infrastructure does not resolve software defects and significantly inflates cloud expenditure.",
            "D": "Disabling alerts creates operational blindness during active outages.",
        },
    ),
    ExamQuestion(
        id="q_pca_019",
        domain_id="domain_6",
        sub_objective_code="6.3",
        difficulty="intermediate",
        case_study_id=None,
        question_text=(
            "You need to store audit logs in Cloud Logging for 7 years to meet regulatory compliance requirements, while minimizing "
            "logging costs. What is the most cost-effective architecture in Google Cloud?"
        ),
        options=[
            QuestionOption(key="A", text="Keep all logs in the default `_Default` Cloud Logging bucket with retention set to 2,555 days."),
            QuestionOption(key="B", text="Create a Log Sink to export audit logs to a Cloud Storage bucket configured with an Object Lifecycle policy transitioning to Archive storage."),
            QuestionOption(key="C", text="Stream all logs continuously into Cloud Spanner database tables."),
            QuestionOption(key="D", text="Export logs to Compute Engine persistent disks mounted to an archival server."),
        ],
        correct_option="B",
        architectural_principle="Cost-Effective Long-Term Log Archival via Cloud Storage Lifecycle",
        explanation=(
            "Cloud Storage Archive class offers the lowest cost per GB-month for long-term compliance data that is rarely accessed. "
            "A Log Sink automatically streams matching audit logs into Cloud Storage without requiring intermediary compute."
        ),
        distractor_analysis={
            "A": "Retaining logs in Cloud Logging buckets for 7 years incurs high storage fees ($0.01/GB/month vs $0.0012/GB/month for Archive).",
            "C": "Cloud Spanner is designed for high-performance transactional SQL, making it prohibitively expensive for cold log storage.",
            "D": "Persistent disks require active VM compute and are significantly more expensive than object storage.",
        },
    ),
]

PCA_FLASHCARDS: List[Flashcard] = [
    Flashcard(
        id="fc_001",
        domain_id="domain_1",
        topic="Database Selection: Spanner vs Bigtable",
        front_prompt="When should you choose Cloud Spanner over Cloud Bigtable?",
        back_solution="Choose Cloud Spanner when you require relational schemas, SQL queries, multi-table ACID transactions, and global multi-region consistency. Choose Bigtable for massive non-relational time-series/IoT data with sub-10ms single-row read/write latency.",
        key_tradeoff="Relational SQL ACID vs Wide-column NoSQL High Throughput",
    ),
    Flashcard(
        id="fc_002",
        domain_id="domain_2",
        topic="Hybrid Connectivity: Dedicated Interconnect vs Cloud VPN",
        front_prompt="When is Dedicated Interconnect required over Cloud VPN?",
        back_solution="Dedicated Interconnect is required when enterprise data bandwidth exceeds 10 Gbps (up to 100 Gbps), requires direct physical BGP routing into Google POPs, and cannot traverse the public internet.",
        key_tradeoff="10Gbps+ private physical link vs public internet IPSec VPN (up to 3Gbps per tunnel)",
    ),
    Flashcard(
        id="fc_003",
        domain_id="domain_3",
        topic="Encryption Keys: CMEK vs CSEK vs Google-Managed",
        front_prompt="What is the difference between CMEK and CSEK on Google Cloud?",
        back_solution="CMEK (Customer-Managed Encryption Keys): Keys are stored and managed in Google Cloud KMS; key rotation and IAM control are managed via GCP. CSEK (Customer-Supplied Encryption Keys): Keys are generated and stored on-prem; you supply the raw key string in every API call, and Google never stores the key.",
        key_tradeoff="GCP Cloud KMS managed key vs Raw customer-provided key string in API payload",
    ),
    Flashcard(
        id="fc_004",
        domain_id="domain_2",
        topic="VPC Design: Shared VPC vs VPC Peering",
        front_prompt="When should you choose Shared VPC over VPC Network Peering?",
        back_solution="Choose Shared VPC when you need a single central organization host network with shared subnets, central firewall management, and unified private IP ranges across projects. Choose VPC Peering for interconnecting two separate decentralized VPC networks without centralized subnet administration.",
        key_tradeoff="Centralized single-network administration vs Decentralized multi-VPC interconnection",
    ),
    Flashcard(
        id="fc_005",
        domain_id="domain_4",
        topic="Deployment Strategies: Canary vs Blue-Green",
        front_prompt="What is the architectural difference between Canary and Blue/Green deployments?",
        back_solution="Canary: Traffic is gradually shifted (e.g. 5% -> 25% -> 100%) to a new release while monitoring error rates and SLIs. Blue/Green: Two identical environments exist simultaneously; 100% of traffic is switched instantly via the load balancer from Blue (old) to Green (new).",
        key_tradeoff="Gradual risk mitigation with traffic splitting vs Instant zero-downtime full switchover",
    ),
    Flashcard(
        id="fc_006",
        domain_id="domain_1",
        topic="Compute Selection: Cloud Run vs GKE vs Compute Engine",
        front_prompt="How do you decide between Cloud Run, GKE, and Compute Engine?",
        back_solution="Cloud Run: Containerized stateless HTTP web apps & microservices scaling automatically from 0 to thousands. GKE: Complex containerized microservices requiring custom networking, service mesh (Istio), daemonsets, stateful workloads, or GPUs. Compute Engine: Legacy non-containerized VMs, specific kernel extensions, or lift-and-shift workloads.",
        key_tradeoff="Serverless simplicity vs Full Kubernetes orchestration control vs Raw OS/VM access",
    ),
    Flashcard(
        id="fc_007",
        domain_id="domain_3",
        topic="Security: Service Accounts & Workload Identity",
        front_prompt="Why is Workload Identity preferred over downloaded Service Account JSON Keys on GKE?",
        back_solution="Workload Identity binds Kubernetes Service Accounts (KSAs) directly to Google Service Accounts (GSAs), eliminating long-lived static JSON credentials that can be leaked or stolen from cluster pods.",
        key_tradeoff="Short-lived secure IAM tokens vs High-risk static downloadable JSON keys",
    ),
    Flashcard(
        id="fc_008",
        domain_id="domain_6",
        topic="SRE: SLI vs SLO vs SLA",
        front_prompt="What is the difference between an SLI, an SLO, and an SLA?",
        back_solution="SLI (Service Level Indicator): A quantifiable metric of service performance (e.g. error rate, p99 latency). SLO (Service Level Objective): Target reliability goal agreed by internal engineering (e.g. 99.9% success rate). SLA (Service Level Agreement): Contractual commitment with financial penalties for breach.",
        key_tradeoff="Actual measurement (SLI) vs Internal Target (SLO) vs External Legal Contract (SLA)",
    ),
    Flashcard(
        id="fc_009",
        domain_id="domain_5",
        topic="Big Data: Dataflow vs Dataproc",
        front_prompt="When should you choose Cloud Dataflow vs Cloud Dataproc?",
        back_solution="Cloud Dataflow: Serverless, auto-scaling Apache Beam unified stream and batch processing without cluster management. Cloud Dataproc: Fast, managed Apache Spark, Hadoop, and Hive clusters when migrating existing Hadoop/Spark code directly to Google Cloud.",
        key_tradeoff="Serverless Apache Beam vs Lift-and-shift Apache Spark/Hadoop clusters",
    ),
]
