import { Db, MongoClient, MongoClientOptions } from "mongodb";
import { env } from "../utils/env";

let client: MongoClient | null = null;
let db: Db | null = null;
let connectPromise: Promise<Db> | null = null;

// MongoDB connection pooling configuration
const mongoOptions: MongoClientOptions = {
  maxPoolSize: parseInt(process.env.MONGO_MAX_POOL_SIZE || '10'),
  minPoolSize: parseInt(process.env.MONGO_MIN_POOL_SIZE || '2'),
  maxIdleTimeMS: 60000,
  serverSelectionTimeoutMS: 5000,
  socketTimeoutMS: 45000,
  retryWrites: process.env.NODE_ENV === 'production',
  retryReads: process.env.NODE_ENV === 'production',
  waitQueueTimeoutMS: 10000,
};

async function initMongo(): Promise<Db> {
  const mongoClient = new MongoClient(env.MONGODB_URI, mongoOptions);
  await mongoClient.connect();

  const database = mongoClient.db(env.MONGODB_DB_NAME);
  await Promise.all([
    database.collection("users").createIndex({ email: 1 }, { unique: true }),
    database.collection("users").createIndex({ id: 1 }, { unique: true }),
    database.collection("resume_analyses").createIndex({ id: 1 }, { unique: true }),
    database.collection("resume_analyses").createIndex({ userId: 1, createdAt: -1 })
  ]);

  client = mongoClient;
  db = database;
  return database;
}

export async function getDatabase(): Promise<Db> {
  if (db) return db;

  if (!connectPromise) {
    connectPromise = initMongo().catch((error) => {
      connectPromise = null;
      throw error;
    });
  }

  return connectPromise;
}

export async function closeMongoConnection() {
  if (!client) return;
  await client.close();
  client = null;
  db = null;
  connectPromise = null;
}
