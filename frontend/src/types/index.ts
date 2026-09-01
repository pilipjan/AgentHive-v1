export interface AgentCreateRequest {
  name: string;
  public_id?: string;
  description?: string;
  model_provider?: string;
  model_name?: string;
  capabilities?: string[];
  system_instructions?: string;
}

export interface AgentSummary {
  id: string;
  public_id: string;
  name: string;
  description?: string;
  model_provider: string;
  model_name: string;
  capabilities: string[];
  status: string;
  reputation_score: number;
  star_rating: number;
  tasks_completed: number;
  successful_tasks: number;
  success_rate: number;
  created_at: string;
}

export interface AgentProfile extends AgentSummary {
  owner_id: string;
  permissions: string[];
  trust_indicators: {
    identity_verified: boolean;
    security_violations: number;
    verification_eligible: boolean;
  };
  updated_at: string;
}

export interface TaskAssignment {
  id: string;
  agent_id: string;
  agent_name: string;
  role: string;
  status: string;
  assigned_at: string;
  completed_at?: string;
}

export interface TaskItem {
  id: string;
  task_id: string;
  title: string;
  description: string;
  requirements: string[];
  status: "CREATED" | "DISCOVERY" | "ASSIGNED" | "RUNNING" | "REVIEW" | "COMPLETED" | "FAILED" | "CANCELLED";
  result?: any;
  max_iterations: number;
  hive_id?: string;
  assigned_agents: TaskAssignment[];
  created_at: string;
  completed_at?: string;
}

export interface HiveMember {
  agent_id: string;
  agent_name: string;
  role_in_hive: string;
  joined_at: string;
}

export interface HiveItem {
  id: string;
  public_id: string;
  name: string;
  description?: string;
  lead_agent_id?: string;
  lead_agent_name?: string;
  task_id?: string;
  status: string;
  members: HiveMember[];
  created_at: string;
}

export interface KnowledgeVerification {
  id: string;
  verifying_agent_id: string;
  verifying_agent_name: string;
  verdict: string;
  evidence?: string;
  timestamp: string;
}

export interface KnowledgeItem {
  id: string;
  summary: string;
  content: string;
  source_agent_id: string;
  source_agent_name: string;
  task_id?: string;
  confidence: number;
  verification_count: number;
  success_count: number;
  failure_count: number;
  visibility: "PRIVATE" | "HIVE" | "PROJECT" | "PUBLIC";
  sensitivity: string;
  tags: string[];
  verdict_distribution: Record<string, number>;
  verifications: KnowledgeVerification[];
  created_at: string;
  last_verified_at?: string;
}

export interface ReputationDetail {
  agent_id: string;
  agent_name: string;
  composite_score: number;
  star_rating: number;
  total_tasks_completed: number;
  successful_tasks: number;
  metrics: {
    task_success_rate: number;
    reviewer_usefulness_score: number;
    verification_accuracy: number;
    reliability_score: number;
    safety_compliance_rate: number;
    security_violations: number;
    evaluations_count: number;
  };
  weight_formula: Record<string, number>;
  verification_eligible: boolean;
}

export interface ReputationEvent {
  id: string;
  event_type: string;
  score_delta: number;
  new_score: number;
  reference_id?: string;
  details: Record<string, any>;
  timestamp: string;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  actor_type: string;
  actor_id: string;
  action: string;
  target_type?: string;
  target_id?: string;
  status: string;
  details: Record<string, any>;
  ip_address?: string;
}
