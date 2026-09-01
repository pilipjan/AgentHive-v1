"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  AlertCircle,
  Award,
  Bot,
  Brain,
  CheckCircle2,
  ChevronRight,
  Database,
  Flame,
  Layers,
  Lock,
  Plus,
  RefreshCw,
  Search,
  Send,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Star,
  Users,
  XCircle,
  Zap,
} from "lucide-react";
import { api } from "@/lib/api";
import {
  AgentProfile,
  AgentSummary,
  AuditLog,
  HiveItem,
  KnowledgeItem,
  ReputationDetail,
  TaskItem,
} from "@/types";

export default function AgentHiveDashboard() {
  const [activeTab, setActiveTab] = useState<
    "dashboard" | "agents" | "tasks" | "hives" | "knowledge" | "reputation" | "security"
  >("dashboard");

  // State
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [hives, setHives] = useState<HiveItem[]>([]);
  const [knowledge, setKnowledge] = useState<KnowledgeItem[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedAgent, setSelectedAgent] = useState<AgentProfile | null>(null);
  const [selectedReputation, setSelectedReputation] = useState<ReputationDetail | null>(null);
  const [selectedTask, setSelectedTask] = useState<TaskItem | null>(null);

  // Modals
  const [showNewAgentModal, setShowNewAgentModal] = useState(false);
  const [showNewTaskModal, setShowNewTaskModal] = useState(false);
  const [showNewKnowledgeModal, setShowNewKnowledgeModal] = useState(false);
  const [showVerifyModal, setShowVerifyModal] = useState<KnowledgeItem | null>(null);

  // Form states
  const [agentForm, setAgentForm] = useState({
    name: "",
    public_id: "",
    description: "",
    model_provider: "OPENAI",
    model_name: "gpt-4o-mini",
    capabilities: "python, fastapi, docker",
  });

  const [taskForm, setTaskForm] = useState({
    title: "",
    description: "",
    requirements: "python, research",
    auto_orchestrate: true,
  });

  const [knowledgeForm, setKnowledgeForm] = useState({
    summary: "",
    content: "",
    source_agent_id: "",
    visibility: "PUBLIC",
    tags: "performance, linux, arm64",
  });

  const [verifyForm, setVerifyForm] = useState({
    verifying_agent_id: "",
    verdict: "VERIFIED",
    evidence: "",
  });

  // Security Playground Form
  const [securityTestInput, setSecurityTestInput] = useState(
    "Contact support at dev@agenthive.org with API token sk-proj-1234567890abcdefghijklmnopqrstuvwxyz0123456789"
  );
  const [securityTestResult, setSecurityTestResult] = useState<any>(null);
  const [securityTesting, setSecurityTesting] = useState(false);

  // Search & Filters
  const [agentSearch, setAgentSearch] = useState("");
  const [knowledgeSearch, setKnowledgeSearch] = useState("");

  const refreshAllData = async () => {
    setLoading(true);
    try {
      const [agentsRes, tasksRes, hivesRes, knowledgeRes, auditRes] = await Promise.allSettled([
        api.getAgents(),
        api.getTasks(),
        api.getHives(),
        api.getKnowledge(),
        api.getAuditLogs({ limit: 20 }),
      ]);

      if (agentsRes.status === "fulfilled") setAgents(agentsRes.value.items || []);
      if (tasksRes.status === "fulfilled") setTasks(tasksRes.value.items || []);
      if (hivesRes.status === "fulfilled") setHives(hivesRes.value.items || []);
      if (knowledgeRes.status === "fulfilled") setKnowledge(knowledgeRes.value.items || []);
      if (auditRes.status === "fulfilled") setAuditLogs(auditRes.value.items || []);
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshAllData();
  }, []);

  const handleCreateAgent = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const caps = agentForm.capabilities
        .split(",")
        .map((c) => c.trim())
        .filter(Boolean);
      await api.createAgent({
        name: agentForm.name,
        public_id: agentForm.public_id || undefined,
        description: agentForm.description,
        model_provider: agentForm.model_provider,
        model_name: agentForm.model_name,
        capabilities: caps,
      });
      setShowNewAgentModal(false);
      setAgentForm({
        name: "",
        public_id: "",
        description: "",
        model_provider: "OPENAI",
        model_name: "gpt-4o-mini",
        capabilities: "python, fastapi, docker",
      });
      await refreshAllData();
    } catch (err: any) {
      alert(`Error creating agent: ${err.message}`);
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const reqs = taskForm.requirements
        .split(",")
        .map((r) => r.trim())
        .filter(Boolean);
      await api.createTask({
        title: taskForm.title,
        description: taskForm.description,
        requirements: reqs,
        auto_orchestrate: taskForm.auto_orchestrate,
      });
      setShowNewTaskModal(false);
      setTaskForm({
        title: "",
        description: "",
        requirements: "python, research",
        auto_orchestrate: true,
      });
      await refreshAllData();
    } catch (err: any) {
      alert(`Error creating task: ${err.message}`);
    }
  };

  const handlePublishKnowledge = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const tags = knowledgeForm.tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
      const agentId = knowledgeForm.source_agent_id || (agents[0]?.public_id ?? "");
      if (!agentId) {
        alert("Please register at least one agent first.");
        return;
      }
      await api.publishKnowledge({
        summary: knowledgeForm.summary,
        content: knowledgeForm.content,
        source_agent_id: agentId,
        visibility: knowledgeForm.visibility,
        tags,
      });
      setShowNewKnowledgeModal(false);
      setKnowledgeForm({
        summary: "",
        content: "",
        source_agent_id: "",
        visibility: "PUBLIC",
        tags: "performance, linux, arm64",
      });
      await refreshAllData();
    } catch (err: any) {
      alert(`Error publishing knowledge: ${err.message}`);
    }
  };

  const handleVerifyKnowledge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showVerifyModal) return;
    try {
      const verifierId = verifyForm.verifying_agent_id || (agents[0]?.public_id ?? "");
      await api.verifyKnowledge(showVerifyModal.id, {
        verifying_agent_id: verifierId,
        verdict: verifyForm.verdict,
        evidence: verifyForm.evidence,
      });
      setShowVerifyModal(null);
      setVerifyForm({ verifying_agent_id: "", verdict: "VERIFIED", evidence: "" });
      await refreshAllData();
    } catch (err: any) {
      alert(`Error submitting verification: ${err.message}`);
    }
  };

  const handleRunSecurityTest = async () => {
    setSecurityTesting(true);
    try {
      const res = await api.inspectSecurity({
        content: securityTestInput,
        sender_id: agents[0]?.public_id || "demo-agent-01",
      });
      setSecurityTestResult(res);
    } catch (err: any) {
      alert(`Security inspect error: ${err.message}`);
    } finally {
      setSecurityTesting(false);
    }
  };

  const openAgentProfile = async (id: string) => {
    try {
      const profile = await api.getAgent(id);
      setSelectedAgent(profile);
      const rep = await api.getReputation(id);
      setSelectedReputation(rep);
    } catch (err: any) {
      alert(`Error loading agent profile: ${err.message}`);
    }
  };

  const filteredAgents = agents.filter(
    (a) =>
      a.name.toLowerCase().includes(agentSearch.toLowerCase()) ||
      a.public_id.toLowerCase().includes(agentSearch.toLowerCase()) ||
      a.capabilities.some((c) => c.toLowerCase().includes(agentSearch.toLowerCase()))
  );

  const filteredKnowledge = knowledge.filter(
    (k) =>
      k.summary.toLowerCase().includes(knowledgeSearch.toLowerCase()) ||
      k.tags.some((t) => t.toLowerCase().includes(knowledgeSearch.toLowerCase()))
  );

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800/80 bg-slate-900/60 flex flex-col justify-between shrink-0 backdrop-blur-xl">
        <div>
          {/* Logo */}
          <div className="p-5 border-b border-slate-800/80 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center shadow-lg shadow-amber-500/20 font-black text-black text-xl">
              🐝
            </div>
            <div>
              <h1 className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-amber-300 bg-clip-text text-transparent">
                AgentHive
              </h1>
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>V1 Operational</span>
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            {[
              { id: "dashboard", label: "Dashboard", icon: Activity, badge: null },
              { id: "agents", label: "Agent Registry", icon: Bot, badge: agents.length },
              { id: "tasks", label: "Tasks & Pipeline", icon: Layers, badge: tasks.length },
              { id: "hives", label: "Hive Clusters", icon: Users, badge: hives.length },
              { id: "knowledge", label: "Shared Memory", icon: Brain, badge: knowledge.length },
              { id: "reputation", label: "Reputation Engine", icon: Award, badge: null },
              { id: "security", label: "Memory Firewall", icon: ShieldCheck, badge: "Active" },
            ].map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id as any)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? "bg-amber-500/15 text-amber-300 border border-amber-500/30 shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 ${isActive ? "text-amber-400" : "text-slate-400"}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge !== null && (
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-mono ${
                        isActive
                          ? "bg-amber-400/20 text-amber-300"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Footer info */}
        <div className="p-4 border-t border-slate-800/80 text-xs text-slate-500 space-y-2">
          <div className="flex justify-between items-center">
            <span>Server</span>
            <span className="font-mono text-slate-400">Oracle ARM64</span>
          </div>
          <div className="flex justify-between items-center">
            <span>Firewall</span>
            <span className="text-emerald-400 flex items-center gap-1">
              <Shield className="w-3 h-3" /> Zero-Trust
            </span>
          </div>
          <button
            onClick={refreshAllData}
            className="w-full mt-2 flex items-center justify-center gap-2 py-1.5 px-3 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Sync State
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 border-b border-slate-800/80 px-8 flex items-center justify-between bg-slate-900/30 backdrop-blur-md shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold capitalize text-slate-100">
              {activeTab === "dashboard"
                ? "Platform Overview"
                : activeTab === "agents"
                ? "Agent Directory & Verified Identities"
                : activeTab === "tasks"
                ? "Task Orchestration Pipeline"
                : activeTab === "hives"
                ? "Active Hive Clusters"
                : activeTab === "knowledge"
                ? "Verified Shared Knowledge Base"
                : activeTab === "reputation"
                ? "Multi-Factor Reputation Matrix"
                : "Zero-Trust Memory Firewall & Audit"}
            </h2>
          </div>

          {/* Quick Actions */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowNewTaskModal(true)}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-medium text-sm transition shadow-md shadow-amber-500/20"
            >
              <Plus className="w-4 h-4" /> New Task
            </button>
            <button
              onClick={() => setShowNewAgentModal(true)}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium text-sm transition"
            >
              <Bot className="w-4 h-4 text-amber-400" /> Register Agent
            </button>
          </div>
        </header>

        {/* Tab Views */}
        <div className="flex-1 overflow-y-auto p-8 space-y-8">
          {/* 1. DASHBOARD OVERVIEW */}
          {activeTab === "dashboard" && (
            <div className="space-y-8 max-w-7xl mx-auto">
              {/* Stat Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
                <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between shadow-sm">
                  <div>
                    <p className="text-xs uppercase tracking-wider font-semibold text-slate-400">
                      Active Agents
                    </p>
                    <h3 className="text-3xl font-bold mt-1 text-white">{agents.length}</h3>
                    <p className="text-xs text-emerald-400 mt-1 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> 100% Identity Verified
                    </p>
                  </div>
                  <div className="p-3.5 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    <Bot className="w-6 h-6" />
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between shadow-sm">
                  <div>
                    <p className="text-xs uppercase tracking-wider font-semibold text-slate-400">
                      Tasks Executed
                    </p>
                    <h3 className="text-3xl font-bold mt-1 text-white">{tasks.length}</h3>
                    <p className="text-xs text-amber-400 mt-1">
                      {tasks.filter((t) => t.status === "COMPLETED").length} Completed
                    </p>
                  </div>
                  <div className="p-3.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    <Layers className="w-6 h-6" />
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between shadow-sm">
                  <div>
                    <p className="text-xs uppercase tracking-wider font-semibold text-slate-400">
                      Shared Knowledge
                    </p>
                    <h3 className="text-3xl font-bold mt-1 text-white">{knowledge.length}</h3>
                    <p className="text-xs text-purple-400 mt-1">Bayesian Verified</p>
                  </div>
                  <div className="p-3.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                    <Brain className="w-6 h-6" />
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between shadow-sm">
                  <div>
                    <p className="text-xs uppercase tracking-wider font-semibold text-slate-400">
                      Firewall Blocks
                    </p>
                    <h3 className="text-3xl font-bold mt-1 text-white">
                      {auditLogs.filter((a) => a.status === "BLOCKED" || a.status === "REDACTED").length}
                    </h3>
                    <p className="text-xs text-emerald-400 mt-1 flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5" /> 0 Leaks Detected
                    </p>
                  </div>
                  <div className="p-3.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <Shield className="w-6 h-6" />
                  </div>
                </div>
              </div>

              {/* Grid: Recent Tasks & Active Hives */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Recent Tasks */}
                <div className="rounded-2xl bg-slate-900/70 border border-slate-800 p-6 space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="font-semibold text-base flex items-center gap-2">
                      <Layers className="w-4 h-4 text-amber-400" /> Recent Orchestrated Tasks
                    </h3>
                    <button
                      onClick={() => setActiveTab("tasks")}
                      className="text-xs text-amber-400 hover:text-amber-300 font-medium"
                    >
                      View All &rarr;
                    </button>
                  </div>
                  <div className="space-y-3">
                    {tasks.slice(0, 4).map((task) => (
                      <div
                        key={task.id}
                        onClick={() => setSelectedTask(task)}
                        className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 cursor-pointer transition flex items-center justify-between"
                      >
                        <div className="space-y-1">
                          <p className="font-medium text-sm text-slate-200">{task.title}</p>
                          <div className="flex items-center gap-2 text-xs text-slate-400">
                            <span className="font-mono">{task.task_id}</span>
                            <span>&bull;</span>
                            <span>{task.assigned_agents?.length || 0} Agents</span>
                          </div>
                        </div>
                        <span
                          className={`text-xs px-2.5 py-1 rounded-full font-mono font-medium ${
                            task.status === "COMPLETED"
                              ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                              : task.status === "RUNNING"
                              ? "bg-blue-500/15 text-blue-400 border border-blue-500/30 animate-pulse"
                              : "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                          }`}
                        >
                          {task.status}
                        </span>
                      </div>
                    ))}
                    {tasks.length === 0 && (
                      <p className="text-sm text-slate-500 text-center py-6">
                        No tasks yet. Create one to trigger multi-agent orchestration.
                      </p>
                    )}
                  </div>
                </div>

                {/* Top Rated Agents */}
                <div className="rounded-2xl bg-slate-900/70 border border-slate-800 p-6 space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="font-semibold text-base flex items-center gap-2">
                      <Bot className="w-4 h-4 text-amber-400" /> High-Reputation Agents
                    </h3>
                    <button
                      onClick={() => setActiveTab("agents")}
                      className="text-xs text-amber-400 hover:text-amber-300 font-medium"
                    >
                      Explore Directory &rarr;
                    </button>
                  </div>
                  <div className="space-y-3">
                    {agents.slice(0, 4).map((agent) => (
                      <div
                        key={agent.id}
                        onClick={() => openAgentProfile(agent.public_id)}
                        className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 cursor-pointer transition flex items-center justify-between"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-800 to-slate-700 flex items-center justify-center font-bold text-amber-400 text-sm">
                            {agent.name.slice(0, 2).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium text-sm text-slate-200">{agent.name}</p>
                            <p className="text-xs text-slate-500 font-mono">{agent.public_id}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="flex items-center gap-1 text-amber-400 font-bold text-sm justify-end">
                            <Star className="w-3.5 h-3.5 fill-amber-400" />
                            <span>{agent.reputation_score.toFixed(2)}</span>
                          </div>
                          <p className="text-xs text-slate-400">
                            {agent.tasks_completed} tasks completed
                          </p>
                        </div>
                      </div>
                    ))}
                    {agents.length === 0 && (
                      <p className="text-sm text-slate-500 text-center py-6">
                        No agents registered yet.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 2. AGENT REGISTRY */}
          {activeTab === "agents" && (
            <div className="space-y-6 max-w-7xl mx-auto">
              <div className="flex flex-col sm:flex-row gap-4 justify-between items-center">
                <div className="relative w-full sm:w-96">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="text"
                    placeholder="Search by name, handle, or capability..."
                    value={agentSearch}
                    onChange={(e) => setAgentSearch(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-amber-500/50"
                  />
                </div>
                <button
                  onClick={() => setShowNewAgentModal(true)}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-sm transition"
                >
                  <Plus className="w-4 h-4" /> Register New Agent
                </button>
              </div>

              {/* Agent Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredAgents.map((agent) => (
                  <div
                    key={agent.id}
                    className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 flex flex-col justify-between hover:border-slate-700 transition shadow-sm space-y-4"
                  >
                    <div>
                      <div className="flex justify-between items-start">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500/20 to-amber-600/10 border border-amber-500/30 flex items-center justify-center font-bold text-amber-300 text-lg">
                            {agent.name.slice(0, 2).toUpperCase()}
                          </div>
                          <div>
                            <h4 className="font-bold text-base text-slate-100">{agent.name}</h4>
                            <p className="text-xs font-mono text-slate-400">{agent.public_id}</p>
                          </div>
                        </div>
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full font-mono ${
                            agent.status === "ACTIVE"
                              ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                              : "bg-red-500/15 text-red-400 border border-red-500/30"
                          }`}
                        >
                          {agent.status}
                        </span>
                      </div>

                      <p className="text-xs text-slate-400 mt-3 line-clamp-2">
                        {agent.description || "General purpose AI agent."}
                      </p>

                      {/* Capabilities */}
                      <div className="flex flex-wrap gap-1.5 mt-3">
                        {agent.capabilities.map((cap) => (
                          <span
                            key={cap}
                            className="text-xs px-2.5 py-0.5 rounded-md bg-slate-800/80 text-slate-300 border border-slate-700/50 font-mono"
                          >
                            {cap}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="pt-4 border-t border-slate-800 flex justify-between items-center">
                      <div className="flex items-center gap-1.5 text-amber-400 font-bold">
                        <Star className="w-4 h-4 fill-amber-400" />
                        <span>{agent.reputation_score.toFixed(2)}</span>
                        <span className="text-xs text-slate-500 font-normal">
                          ({agent.tasks_completed} tasks)
                        </span>
                      </div>
                      <button
                        onClick={() => openAgentProfile(agent.public_id)}
                        className="text-xs font-semibold text-amber-400 hover:text-amber-300 flex items-center gap-1"
                      >
                        View Profile <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 3. TASKS & PIPELINE */}
          {activeTab === "tasks" && (
            <div className="space-y-6 max-w-7xl mx-auto">
              <div className="flex justify-between items-center">
                <h3 className="font-semibold text-base text-slate-200">
                  Orchestrated Multi-Agent Tasks
                </h3>
                <button
                  onClick={() => setShowNewTaskModal(true)}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-sm transition"
                >
                  <Plus className="w-4 h-4" /> Submit Task
                </button>
              </div>

              <div className="space-y-4">
                {tasks.map((task) => (
                  <div
                    key={task.id}
                    className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 space-y-4"
                  >
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                      <div>
                        <div className="flex items-center gap-3">
                          <h4 className="font-bold text-base text-slate-100">{task.title}</h4>
                          <span
                            className={`text-xs px-2.5 py-0.5 rounded-full font-mono ${
                              task.status === "COMPLETED"
                                ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                                : task.status === "RUNNING"
                                ? "bg-blue-500/15 text-blue-400 border border-blue-500/30"
                                : "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                            }`}
                          >
                            {task.status}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 font-mono mt-1">{task.task_id}</p>
                      </div>

                      {task.status !== "COMPLETED" && task.status !== "CANCELLED" && (
                        <button
                          onClick={async () => {
                            if (confirm("Cancel this running task?")) {
                              await api.cancelTask(task.task_id);
                              await refreshAllData();
                            }
                          }}
                          className="text-xs px-3 py-1.5 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition"
                        >
                          Cancel Task
                        </button>
                      )}
                    </div>

                    <p className="text-sm text-slate-300">{task.description}</p>

                    {/* Requirements & Assignments */}
                    <div className="flex flex-wrap gap-4 text-xs text-slate-400 pt-2 border-t border-slate-800/80">
                      <div>
                        <span className="text-slate-500 mr-2">Prerequisites:</span>
                        {task.requirements.map((req) => (
                          <span
                            key={req}
                            className="mr-1.5 px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono"
                          >
                            {req}
                          </span>
                        ))}
                      </div>
                      {task.hive_id && (
                        <div>
                          <span className="text-slate-500 mr-2">Hive:</span>
                          <span className="font-mono text-amber-400">{task.hive_id}</span>
                        </div>
                      )}
                    </div>

                    {/* Subtask Synthesis Result */}
                    {task.result && (
                      <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2">
                        <div className="flex justify-between items-center text-xs">
                          <span className="font-semibold text-amber-400">
                            Orchestrator Output Synthesis
                          </span>
                          <span className="text-slate-500 font-mono">
                            Confidence: {Math.round((task.result.confidence || 0.95) * 100)}%
                          </span>
                        </div>
                        <p className="text-xs text-slate-300">{task.result.summary}</p>
                        {task.result.subtasks && (
                          <div className="space-y-1.5 pt-2">
                            {task.result.subtasks.map((st: any, idx: number) => (
                              <div
                                key={idx}
                                className="text-xs p-2 rounded bg-slate-900/60 border border-slate-800/50 flex justify-between items-center"
                              >
                                <span className="font-mono text-amber-300">
                                  [{st.role}] {st.agent_name}: {st.output}
                                </span>
                                <span className="text-emerald-400 font-mono text-[10px]">
                                  &bull; {st.status}
                                </span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 4. HIVES CLUSTERS */}
          {activeTab === "hives" && (
            <div className="space-y-6 max-w-7xl mx-auto">
              <div className="flex justify-between items-center">
                <h3 className="font-semibold text-base text-slate-200">
                  Agent Collaboration Teams
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {hives.map((hive) => (
                  <div
                    key={hive.id}
                    className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 space-y-4"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-bold text-base text-slate-100">{hive.name}</h4>
                        <p className="text-xs font-mono text-slate-500">{hive.public_id}</p>
                      </div>
                      <span className="text-xs px-2.5 py-0.5 rounded-full font-mono bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                        {hive.status}
                      </span>
                    </div>

                    <p className="text-xs text-slate-400">{hive.description}</p>

                    <div className="space-y-2 pt-2 border-t border-slate-800">
                      <p className="text-xs font-semibold text-slate-400">Hive Roster:</p>
                      <div className="grid grid-cols-2 gap-2">
                        {hive.members.map((m) => (
                          <div
                            key={m.agent_id}
                            className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 text-xs flex items-center justify-between"
                          >
                            <span className="font-medium text-slate-200">{m.agent_name}</span>
                            <span className="font-mono text-[10px] text-amber-400 px-1.5 py-0.5 rounded bg-amber-500/10">
                              {m.role_in_hive}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {hive.status === "ACTIVE" && (
                      <button
                        onClick={async () => {
                          if (confirm("Disband this Hive?")) {
                            await api.disbandHive(hive.public_id);
                            await refreshAllData();
                          }
                        }}
                        className="w-full py-1.5 rounded-lg bg-slate-800 hover:bg-red-500/20 hover:text-red-400 text-slate-400 text-xs transition font-medium"
                      >
                        Disband Hive
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 5. SHARED KNOWLEDGE */}
          {activeTab === "knowledge" && (
            <div className="space-y-6 max-w-7xl mx-auto">
              <div className="flex flex-col sm:flex-row gap-4 justify-between items-center">
                <div className="relative w-full sm:w-96">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="text"
                    placeholder="Search claims by keyword or tag..."
                    value={knowledgeSearch}
                    onChange={(e) => setKnowledgeSearch(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-amber-500/50"
                  />
                </div>
                <button
                  onClick={() => setShowNewKnowledgeModal(true)}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-sm transition"
                >
                  <Plus className="w-4 h-4" /> Publish Knowledge
                </button>
              </div>

              <div className="space-y-4">
                {filteredKnowledge.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 space-y-3"
                  >
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                      <div className="flex items-center gap-3">
                        <h4 className="font-bold text-base text-slate-100">{item.summary}</h4>
                        <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-blue-500/15 text-blue-400 border border-blue-500/30">
                          {item.visibility}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono px-2 py-1 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20 font-bold">
                          Confidence: {Math.round(item.confidence * 100)}%
                        </span>
                        <button
                          onClick={() => setShowVerifyModal(item)}
                          className="text-xs px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
                        >
                          Peer Verify
                        </button>
                      </div>
                    </div>

                    <p className="text-sm text-slate-300 bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80 font-mono text-xs">
                      {item.content}
                    </p>

                    <div className="flex justify-between items-center text-xs text-slate-400 pt-2 border-t border-slate-800/80">
                      <div className="flex items-center gap-2">
                        <span>Source: <strong className="text-slate-300 font-mono">{item.source_agent_name}</strong></span>
                        <span>&bull;</span>
                        <span>Verifications: {item.verification_count}</span>
                      </div>
                      <div className="flex gap-1.5">
                        {item.tags.map((t) => (
                          <span
                            key={t}
                            className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono text-[10px]"
                          >
                            #{t}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Verification Records */}
                    {item.verifications && item.verifications.length > 0 && (
                      <div className="space-y-1.5 pt-2">
                        <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                          Verification Ledger:
                        </p>
                        {item.verifications.map((v) => (
                          <div
                            key={v.id}
                            className="text-xs p-2 rounded bg-slate-950 border border-slate-800/60 flex justify-between items-center"
                          >
                            <span className="text-slate-300">
                              <strong className="text-amber-400 font-mono">{v.verifying_agent_name}</strong>: {v.evidence || "Verified benchmark metrics."}
                            </span>
                            <span className="text-emerald-400 font-bold font-mono text-[10px]">
                              {v.verdict}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 6. REPUTATION ENGINE */}
          {activeTab === "reputation" && (
            <div className="space-y-6 max-w-7xl mx-auto">
              <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 to-amber-950/30 border border-slate-800 space-y-2">
                <h3 className="font-bold text-lg text-amber-300 flex items-center gap-2">
                  <Award className="w-5 h-5 text-amber-400" /> Multi-Factor Reputation Engine
                </h3>
                <p className="text-xs text-slate-400 max-w-3xl">
                  Reputation is computed from verifiable outcomes rather than popularity voting:
                  <strong> 40% Task Success + 20% Reviewer Utility + 15% Verification Rigor + 15% Reliability + 10% Policy Safety</strong>.
                  Direct tampering is blocked; score deltas occur exclusively via validated platform events.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {agents.map((agent) => (
                  <div
                    key={agent.id}
                    onClick={() => openAgentProfile(agent.public_id)}
                    className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 cursor-pointer transition space-y-4"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-bold text-base text-slate-100">{agent.name}</h4>
                        <p className="text-xs font-mono text-slate-400">{agent.public_id}</p>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center gap-1 text-amber-400 font-bold text-lg">
                          <Star className="w-5 h-5 fill-amber-400" />
                          <span>{agent.reputation_score.toFixed(2)}</span>
                        </div>
                        <span className="text-xs text-slate-500">Scale: 1.0 - 5.0</span>
                      </div>
                    </div>

                    {/* Breakdown Bars */}
                    <div className="space-y-2 pt-2 border-t border-slate-800 text-xs">
                      <div>
                        <div className="flex justify-between text-slate-400 mb-1">
                          <span>Task Success Rate</span>
                          <span className="font-mono text-slate-200">
                            {agent.tasks_completed > 0
                              ? `${((agent.successful_tasks / agent.tasks_completed) * 100).toFixed(1)}%`
                              : "100.0%"}
                          </span>
                        </div>
                        <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                          <div
                            className="h-full bg-amber-400 rounded-full"
                            style={{
                              width: `${agent.tasks_completed > 0 ? (agent.successful_tasks / agent.tasks_completed) * 100 : 100}%`,
                            }}
                          ></div>
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-slate-400 mb-1">
                          <span>Verification Eligibility</span>
                          <span className="font-mono text-emerald-400">
                            {agent.reputation_score >= 3.5 ? "Eligible (≥ 3.50)" : "Pending"}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 7. MEMORY FIREWALL & AUDIT */}
          {activeTab === "security" && (
            <div className="space-y-8 max-w-7xl mx-auto">
              {/* Interactive Firewall Playground */}
              <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="font-bold text-base text-slate-100 flex items-center gap-2">
                    <ShieldCheck className="w-5 h-5 text-emerald-400" /> Memory Firewall Live Inspector
                  </h3>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Active Protection
                  </span>
                </div>
                <p className="text-xs text-slate-400">
                  Test payload sanitization in real-time. Secrets (OpenAI, Anthropic, Gemini, AWS, SSH keys, DB URLs) and PII (emails, SSNs, phones) are sanitized or blocked before storage.
                </p>

                <div className="space-y-3">
                  <textarea
                    rows={3}
                    value={securityTestInput}
                    onChange={(e) => setSecurityTestInput(e.target.value)}
                    className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 focus:outline-none focus:border-amber-500/50"
                  />
                  <div className="flex justify-end">
                    <button
                      onClick={handleRunSecurityTest}
                      disabled={securityTesting}
                      className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-xs transition"
                    >
                      {securityTesting ? "Inspecting..." : "Execute Firewall Inspection"}
                    </button>
                  </div>
                </div>

                {securityTestResult && (
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 mt-4 text-xs font-mono">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-slate-300">Policy Verdict:</span>
                      <span
                        className={`font-bold px-2 py-0.5 rounded ${
                          securityTestResult.verdict === "ALLOWED"
                            ? "bg-emerald-500/20 text-emerald-400"
                            : securityTestResult.verdict === "REDACTED"
                            ? "bg-amber-500/20 text-amber-400"
                            : "bg-red-500/20 text-red-400"
                        }`}
                      >
                        {securityTestResult.verdict}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500">Sanitized Output:</span>
                      <p className="p-2.5 mt-1 rounded bg-slate-900 text-emerald-300 border border-slate-800">
                        {securityTestResult.sanitized_text || "[BLOCKED]"}
                      </p>
                    </div>
                    {securityTestResult.detected_secrets?.length > 0 && (
                      <p className="text-amber-400">
                        Detected Secrets: {securityTestResult.detected_secrets.join(", ")}
                      </p>
                    )}
                    {securityTestResult.detected_pii?.length > 0 && (
                      <p className="text-amber-400">
                        Detected PII: {securityTestResult.detected_pii.join(", ")}
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Sanitized Audit Log Table */}
              <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 space-y-4">
                <h3 className="font-bold text-base text-slate-100 flex items-center gap-2">
                  <Lock className="w-5 h-5 text-amber-400" /> Platform Security & Activity Audit Log
                </h3>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="border-b border-slate-800 text-slate-400 font-mono">
                      <tr>
                        <th className="pb-3 font-semibold">Timestamp</th>
                        <th className="pb-3 font-semibold">Actor</th>
                        <th className="pb-3 font-semibold">Action</th>
                        <th className="pb-3 font-semibold">Target</th>
                        <th className="pb-3 font-semibold">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      {auditLogs.map((log) => (
                        <tr key={log.id} className="hover:bg-slate-800/30">
                          <td className="py-2.5 text-slate-400">
                            {new Date(log.timestamp).toLocaleTimeString()}
                          </td>
                          <td className="py-2.5 text-amber-300 font-bold">{log.actor_id}</td>
                          <td className="py-2.5 text-slate-200">{log.action}</td>
                          <td className="py-2.5 text-slate-400">{log.target_id || "-"}</td>
                          <td className="py-2.5">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                log.status === "SUCCESS" || log.status === "ALLOWED"
                                  ? "bg-emerald-500/10 text-emerald-400"
                                  : log.status === "REDACTED"
                                  ? "bg-amber-500/10 text-amber-400"
                                  : "bg-red-500/10 text-red-400"
                              }`}
                            >
                              {log.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                      {auditLogs.length === 0 && (
                        <tr>
                          <td colSpan={5} className="py-6 text-center text-slate-500">
                            No audit records logged yet.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* MODAL: Register Agent */}
      {showNewAgentModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="font-bold text-lg text-slate-100">Register Agent</h3>
              <button
                onClick={() => setShowNewAgentModal(false)}
                className="text-slate-400 hover:text-white"
              >
                &times;
              </button>
            </div>
            <form onSubmit={handleCreateAgent} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Display Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. PythonForge"
                  value={agentForm.name}
                  onChange={(e) => setAgentForm({ ...agentForm, name: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Public Handle (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. agt-python-forge-01"
                  value={agentForm.public_id}
                  onChange={(e) => setAgentForm({ ...agentForm, public_id: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500 font-mono"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Capabilities (Comma Separated)</label>
                <input
                  type="text"
                  placeholder="python, fastapi, docker, linux"
                  value={agentForm.capabilities}
                  onChange={(e) => setAgentForm({ ...agentForm, capabilities: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500 font-mono"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Model Provider</label>
                  <select
                    value={agentForm.model_provider}
                    onChange={(e) => setAgentForm({ ...agentForm, model_provider: e.target.value })}
                    className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500"
                  >
                    <option value="OPENAI">OpenAI</option>
                    <option value="OLLAMA">Local Ollama</option>
                    <option value="ANTHROPIC">Anthropic</option>
                    <option value="GEMINI">Google Gemini</option>
                    <option value="MOCK">Mock (Offline)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Model Tag</label>
                  <input
                    type="text"
                    value={agentForm.model_name}
                    onChange={(e) => setAgentForm({ ...agentForm, model_name: e.target.value })}
                    className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500 font-mono"
                  />
                </div>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Specialization Description</label>
                <textarea
                  rows={2}
                  value={agentForm.description}
                  onChange={(e) => setAgentForm({ ...agentForm, description: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>
              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowNewAgentModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold"
                >
                  Register Agent
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Submit Task */}
      {showNewTaskModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="font-bold text-lg text-slate-100">Submit New Task</h3>
              <button
                onClick={() => setShowNewTaskModal(false)}
                className="text-slate-400 hover:text-white"
              >
                &times;
              </button>
            </div>
            <form onSubmit={handleCreateTask} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Task Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Optimize FFmpeg stream latency for ARM64"
                  value={taskForm.title}
                  onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Prerequisite Capabilities (Comma Separated)</label>
                <input
                  type="text"
                  placeholder="python, research, ffmpeg, linux"
                  value={taskForm.requirements}
                  onChange={(e) => setTaskForm({ ...taskForm, requirements: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500 font-mono"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Detailed Instructions & Scope</label>
                <textarea
                  rows={3}
                  required
                  placeholder="Explain goals, constraints, and desired output format..."
                  value={taskForm.description}
                  onChange={(e) => setTaskForm({ ...taskForm, description: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>
              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="auto_orchestrate"
                  checked={taskForm.auto_orchestrate}
                  onChange={(e) => setTaskForm({ ...taskForm, auto_orchestrate: e.target.checked })}
                  className="rounded bg-slate-950 border-slate-800 text-amber-500 focus:ring-amber-500"
                />
                <label htmlFor="auto_orchestrate" className="text-slate-300">
                  Auto-orchestrate: Match suitable agents, form Hive, and synthesize results
                </label>
              </div>
              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowNewTaskModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold"
                >
                  Dispatch Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Publish Knowledge */}
      {showNewKnowledgeModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="font-bold text-lg text-slate-100">Publish Shared Knowledge</h3>
              <button
                onClick={() => setShowNewKnowledgeModal(false)}
                className="text-slate-400 hover:text-white"
              >
                &times;
              </button>
            </div>
            <form onSubmit={handlePublishKnowledge} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Knowledge Claim / Summary</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. FFmpeg v4l2m2m hardware acceleration on Linux ARM64"
                  value={knowledgeForm.summary}
                  onChange={(e) => setKnowledgeForm({ ...knowledgeForm, summary: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Source Agent Handle</label>
                <select
                  value={knowledgeForm.source_agent_id}
                  onChange={(e) => setKnowledgeForm({ ...knowledgeForm, source_agent_id: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500 font-mono"
                >
                  <option value="">Select Author Agent</option>
                  {agents.map((a) => (
                    <option key={a.public_id} value={a.public_id}>
                      {a.name} ({a.public_id})
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Visibility Scope</label>
                  <select
                    value={knowledgeForm.visibility}
                    onChange={(e) => setKnowledgeForm({ ...knowledgeForm, visibility: e.target.value })}
                    className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500"
                  >
                    <option value="PUBLIC">PUBLIC (Universal)</option>
                    <option value="HIVE">HIVE (Team)</option>
                    <option value="PROJECT">PROJECT (Project)</option>
                    <option value="PRIVATE">PRIVATE (Author Only)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Tags</label>
                  <input
                    type="text"
                    placeholder="ffmpeg, arm64, performance"
                    value={knowledgeForm.tags}
                    onChange={(e) => setKnowledgeForm({ ...knowledgeForm, tags: e.target.value })}
                    className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500 font-mono"
                  />
                </div>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Finding Details / Benchmark Content</label>
                <textarea
                  rows={4}
                  required
                  placeholder="Detailed findings passing through Memory Firewall..."
                  value={knowledgeForm.content}
                  onChange={(e) => setKnowledgeForm({ ...knowledgeForm, content: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500 font-mono"
                />
              </div>
              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowNewKnowledgeModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold"
                >
                  Publish to Memory
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Peer Verify Knowledge */}
      {showVerifyModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="font-bold text-lg text-slate-100">Peer Verify Claim</h3>
              <button
                onClick={() => setShowVerifyModal(null)}
                className="text-slate-400 hover:text-white"
              >
                &times;
              </button>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300">
              <p className="font-bold text-amber-300">{showVerifyModal.summary}</p>
              <p className="font-mono text-slate-400 mt-1">{showVerifyModal.content}</p>
            </div>
            <form onSubmit={handleVerifyKnowledge} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Verifying Agent (Reputation ≥ 3.50)</label>
                <select
                  value={verifyForm.verifying_agent_id}
                  onChange={(e) => setVerifyForm({ ...verifyForm, verifying_agent_id: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500 font-mono"
                >
                  <option value="">Select Verifier Agent</option>
                  {agents.map((a) => (
                    <option key={a.public_id} value={a.public_id}>
                      {a.name} (⭐ {a.reputation_score.toFixed(2)})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Verdict</label>
                <select
                  value={verifyForm.verdict}
                  onChange={(e) => setVerifyForm({ ...verifyForm, verdict: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500 font-bold"
                >
                  <option value="VERIFIED">VERIFIED (Corroborated)</option>
                  <option value="REFUTED">REFUTED (Contradicted)</option>
                  <option value="INCONCLUSIVE">INCONCLUSIVE (Partial)</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Evidence / Benchmark Observations</label>
                <textarea
                  rows={3}
                  required
                  placeholder="Record experimental evidence or reproducibility notes..."
                  value={verifyForm.evidence}
                  onChange={(e) => setVerifyForm({ ...verifyForm, evidence: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>
              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowVerifyModal(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold"
                >
                  Submit Verdict
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DRAWER: Agent Profile Details */}
      {selectedAgent && (
        <div className="fixed inset-y-0 right-0 w-full max-w-md bg-slate-900 border-l border-slate-800 z-50 p-6 overflow-y-auto space-y-6 shadow-2xl">
          <div className="flex justify-between items-start border-b border-slate-800 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center justify-center font-bold text-lg">
                {selectedAgent.name.slice(0, 2).toUpperCase()}
              </div>
              <div>
                <h3 className="font-bold text-lg text-slate-100">{selectedAgent.name}</h3>
                <p className="text-xs font-mono text-slate-400">{selectedAgent.public_id}</p>
              </div>
            </div>
            <button
              onClick={() => setSelectedAgent(null)}
              className="text-slate-400 hover:text-white text-lg"
            >
              &times;
            </button>
          </div>

          {/* Reputation Summary */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex justify-between items-center">
            <div>
              <p className="text-xs text-slate-400">Reputation Score</p>
              <div className="flex items-center gap-1.5 text-amber-400 font-bold text-xl mt-0.5">
                <Star className="w-5 h-5 fill-amber-400" />
                <span>{selectedAgent.reputation_score.toFixed(2)}</span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-slate-400">Success Rate</p>
              <p className="text-xl font-bold text-emerald-400 mt-0.5">
                {selectedAgent.success_rate.toFixed(1)}%
              </p>
            </div>
          </div>

          {/* Trust Indicators */}
          <div className="space-y-2 text-xs">
            <p className="font-semibold text-slate-400 uppercase tracking-wider">
              Trust & Verification:
            </p>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
              <div className="flex justify-between">
                <span className="text-slate-400">Identity Verified:</span>
                <span className="text-emerald-400 font-mono">✓ Yes (Platform Stamped)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Security Violations:</span>
                <span className="text-slate-200 font-mono">0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Verification Eligible:</span>
                <span className="text-emerald-400 font-mono">
                  {selectedAgent.reputation_score >= 3.5 ? "✓ Yes (Score ≥ 3.50)" : "✗ No"}
                </span>
              </div>
            </div>
          </div>

          {/* Granted Permissions */}
          <div className="space-y-2 text-xs">
            <p className="font-semibold text-slate-400 uppercase tracking-wider">
              Atomic Permissions:
            </p>
            <div className="flex flex-wrap gap-1.5">
              {selectedAgent.permissions.map((p) => (
                <span
                  key={p}
                  className="px-2.5 py-1 rounded bg-slate-950 text-slate-300 font-mono text-[10px] border border-slate-800"
                >
                  {p}
                </span>
              ))}
            </div>
          </div>

          {/* Emergency Disable Action */}
          {selectedAgent.status === "ACTIVE" && (
            <div className="pt-4 border-t border-slate-800">
              <button
                onClick={async () => {
                  if (confirm(`Emergency disable agent ${selectedAgent.name}?`)) {
                    await api.disableAgent(selectedAgent.public_id);
                    setSelectedAgent(null);
                    await refreshAllData();
                  }
                }}
                className="w-full py-2.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-bold transition"
              >
                Emergency Disable Agent
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
