import { gql } from "@apollo/client";

export const LOGIN = gql`
  mutation Login($username: String!, $password: String!) {
    login(username: $username, password: $password) {
      accessToken
      refreshToken
      tokenType
    }
  }
`;

export const VIEWER = gql`
  query Viewer {
    viewer {
      id
      username
      email
      roles
      isActive
    }
  }
`;

export const SYSTEM_HEALTH = gql`
  query SystemHealth {
    systemHealth {
      status
      service
      version
      uptimeSeconds
    }
  }
`;

export const JOBS = gql`
  query Jobs($limit: Int) {
    jobs(limit: $limit) {
      jobId
      taskId
      type
      status
      progress
      message
      createdAt
    }
  }
`;

export const START_JOB = gql`
  mutation StartJob($input: StartJobInput!) {
    startJob(input: $input) {
      jobId
      taskId
      type
      status
      progress
      message
      createdAt
    }
  }
`;

export const JOB_PROGRESS = gql`
  subscription JobProgress($jobId: ID!) {
    jobProgress(jobId: $jobId) {
      jobId
      status
      progress
      message
      timestamp
    }
  }
`;

export const RAG_STATUS = gql`
  query RagStatus {
    ragStatus {
      status
      docsCount
      chunksCount
    }
  }
`;

export const QUERY_RAG = gql`
  mutation QueryRag($query: String!, $topK: Int, $returnChunks: Boolean) {
    queryRag(query: $query, topK: $topK, returnChunks: $returnChunks) {
      status
      answer
      citations
      retrieval
    }
  }
`;

export const RUN_RISK = gql`
  mutation RunRisk($input: RiskInput!) {
    runRisk(input: $input) {
      cyberRisk
      behaviorRisk
      fraudRisk
      fusionRisk
      decision
      reasonCode
      explanation
    }
  }
`;

export const SCORE_FRAUD = gql`
  mutation ScoreFraud($features: [Float!]!) {
    scoreFraud(features: $features) {
      score
      inputFeatures
      expectedFeatures
    }
  }
`;

export const SCORE_CYBER = gql`
  mutation ScoreCyber($features: [Float!]!) {
    scoreCyber(features: $features) {
      score
      inputFeatures
      expectedFeatures
    }
  }
`;

export const SCORE_BEHAVIOR = gql`
  mutation ScoreBehavior($features: [Float!]!) {
    scoreBehavior(features: $features) {
      score
      inputFeatures
      expectedFeatures
    }
  }
`;

export const MODELS = gql`
  query Models {
    models {
      id
      modelName
      version
      status
      createdAt
    }
  }
`;

export const DATASETS = gql`
  query Datasets {
    datasets {
      id
      name
      location
      license
      sizeBytes
      createdAt
    }
  }
`;

export const CREATE_UPLOAD_SESSION = gql`
  mutation CreateUploadSession($input: UploadSessionInput!) {
    createUploadSession(input: $input) {
      uploadUrl
      objectKey
      expiresAt
      maxBytes
      contentTypes
    }
  }
`;

export const FINALIZE_UPLOAD = gql`
  mutation FinalizeUpload($input: FinalizeUploadInput!) {
    finalizeUpload(input: $input) {
      status
      objectKey
      correlationId
      jobId
    }
  }
`;

export const INFERENCE_TRACE = gql`
  subscription InferenceTrace($correlationId: String!) {
    inferenceTrace(correlationId: $correlationId) {
      correlationId
      step
      status
      message
      timestamp
      latencyMs
    }
  }
`;

export const SYSTEM_ALERTS = gql`
  subscription SystemAlerts {
    systemAlerts {
      level
      message
      component
      timestamp
    }
  }
`;

export const DASHBOARD_SUMMARY = gql`
  query DashboardSummary {
    dashboardSummary {
      fraudAlerts
      docsIndexed
      activeJobs
      riskScore
      alerts {
        level
        message
        component
        timestamp
      }
    }
  }
`;

export const TRAINING_OVERVIEW = gql`
  query TrainingOverview {
    trainingOverview {
      generatedAt
      readyCount
      totalCount
      domains {
        domain
        status
        datasetReady
        modelReady
        sourcePath
        updatedAt
        blockers
        metrics {
          accuracy
          f1
          auc
          precision
          recall
        }
      }
    }
  }
`;

export const TRAINING_DOMAIN = gql`
  query TrainingDomain($domain: String!) {
    trainingDomain(domain: $domain) {
      domain
      status
      datasetReady
      modelReady
      sourcePath
      updatedAt
      blockers
      metrics {
        accuracy
        f1
        auc
        precision
        recall
      }
    }
  }
`;

export const MISSION_CHAT = gql`
  mutation MissionChat($prompt: String!, $useRag: Boolean) {
    missionChat(prompt: $prompt, useRag: $useRag)
  }
`;

export const RECOMMEND_MOVIES = gql`
  mutation RecommendMovies($prompt: String!, $topK: Int) {
    recommendMovies(prompt: $prompt, topK: $topK) {
      mode
      items {
        id
        title
        score
        reason
      }
      raw
    }
  }
`;

export const RECOMMEND_CLOTHES = gql`
  mutation RecommendClothes($prompt: String!, $topK: Int) {
    recommendClothes(prompt: $prompt, topK: $topK) {
      mode
      items {
        id
        title
        score
        reason
      }
      raw
    }
  }
`;

export const ANALYZE_VOICE_EMOTION = gql`
  mutation AnalyzeVoiceEmotion($input: MediaAnalyzeInput!) {
    analyzeVoiceEmotion(input: $input)
  }
`;

export const ANALYZE_VIDEO_EMOTION = gql`
  mutation AnalyzeVideoEmotion($input: MediaAnalyzeInput!) {
    analyzeVideoEmotion(input: $input)
  }
`;

export const DETECT_DEEPFAKE = gql`
  mutation DetectDeepfake($input: MediaAnalyzeInput!) {
    detectDeepfake(input: $input)
  }
`;

export const DETECT_BRAND_LOGOS = gql`
  mutation DetectBrandLogos($input: MediaAnalyzeInput!) {
    detectBrandLogos(input: $input)
  }
`;
