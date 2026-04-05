import { print } from "graphql";
import {
  CREATE_UPLOAD_SESSION,
  FINALIZE_UPLOAD,
  JOB_PROGRESS,
  JOBS,
  LOGIN,
  QUERY_RAG,
  RUN_RISK,
  TRAINING_DOMAIN,
  TRAINING_OVERVIEW,
  SYSTEM_ALERTS,
  SYSTEM_HEALTH,
  VIEWER,
} from "./gateway-graphql";

describe("gateway GraphQL operations", () => {
  it("defines core query and mutation documents", () => {
    expect(print(LOGIN)).toContain("mutation Login");
    expect(print(VIEWER)).toContain("query Viewer");
    expect(print(SYSTEM_HEALTH)).toContain("query SystemHealth");
    expect(print(JOBS)).toContain("query Jobs");
    expect(print(QUERY_RAG)).toContain("mutation QueryRag");
    expect(print(RUN_RISK)).toContain("mutation RunRisk");
  });

  it("defines upload and subscription documents", () => {
    expect(print(CREATE_UPLOAD_SESSION)).toContain("mutation CreateUploadSession");
    expect(print(FINALIZE_UPLOAD)).toContain("mutation FinalizeUpload");
    expect(print(JOB_PROGRESS)).toContain("subscription JobProgress");
    expect(print(SYSTEM_ALERTS)).toContain("subscription SystemAlerts");
  });

  it("defines training readiness documents", () => {
    expect(print(TRAINING_OVERVIEW)).toContain("query TrainingOverview");
    expect(print(TRAINING_DOMAIN)).toContain("query TrainingDomain");
  });
});
