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
    # Domain 1 Question (Mountkirk Games Case Study)
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
    # Domain 2 Question (Networking / Hybrid)
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
    # Domain 3 Question (Security & Compliance - EHR Healthcare)
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
    # Domain 4 Question (Technical Processes / CI/CD)
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
    # Domain 5 Question (Implementation / Architecture)
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
    # Domain 6 Question (Reliability / SRE)
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
]
