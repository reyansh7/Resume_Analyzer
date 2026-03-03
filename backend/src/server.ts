import { app } from "./app";
import { closeMongoConnection } from "./services/mongodb";
import { env } from "./utils/env";

const server = app.listen(env.PORT, () => {
  console.log(`Backend running on port ${env.PORT}`);
});

async function shutdown(signal: string) {
  console.log(`Received ${signal}. Shutting down backend...`);
  server.close(async () => {
    await closeMongoConnection();
    process.exit(0);
  });
}

process.on("SIGINT", () => {
  void shutdown("SIGINT");
});

process.on("SIGTERM", () => {
  void shutdown("SIGTERM");
});
