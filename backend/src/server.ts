import { app } from "./app";
import { closeMongoConnection } from "./services/mongodb";
import { env } from "./utils/env";

// Global error handlers
process.on('unhandledRejection', (reason: unknown, promise: Promise<any>) => {
  console.error('[ERROR] Unhandled Rejection:', {
    reason: reason instanceof Error ? reason.message : String(reason),
    stack: reason instanceof Error ? reason.stack : undefined,
  });
  process.exit(1);
});

process.on('uncaughtException', (error: Error) => {
  console.error('[ERROR] Uncaught Exception:', {
    message: error.message,
    stack: error.stack,
  });
  process.exit(1);
});

const server = app.listen(env.PORT, () => {
  console.log(`[INFO] Backend running on port ${env.PORT}`);
});

async function shutdown(signal: string) {
  console.log(`[INFO] Received ${signal}. Shutting down backend...`);
  server.close(async () => {
    try {
      await closeMongoConnection();
    } catch (error) {
      console.error('[ERROR] Error closing MongoDB:', error);
    }
    process.exit(0);
  });
  
  // Force shutdown after 10 seconds
  setTimeout(() => {
    console.error('[ERROR] Forced shutdown due to timeout');
    process.exit(1);
  }, 10000);
}

process.on("SIGINT", () => {
  void shutdown("SIGINT");
});

process.on("SIGTERM", () => {
  void shutdown("SIGTERM");
});

process.on("SIGABRT", () => {
  void shutdown("SIGABRT");
});
