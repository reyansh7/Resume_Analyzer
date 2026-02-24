import { PrismaClient } from "@prisma/client";

function normalizeDatabaseUrlForPrisma() {
	const raw = process.env.DATABASE_URL;
	if (!raw) return;

	try {
		const parsed = new URL(raw);
		const isSupabasePooler = parsed.hostname.endsWith("pooler.supabase.com") || parsed.port === "6543";

		if (!isSupabasePooler) return;

		if (!parsed.searchParams.has("pgbouncer")) {
			parsed.searchParams.set("pgbouncer", "true");
		}

		if (!parsed.searchParams.has("connection_limit")) {
			parsed.searchParams.set("connection_limit", "1");
		}

		process.env.DATABASE_URL = parsed.toString();
	} catch {
		return;
	}
}

normalizeDatabaseUrlForPrisma();

export const prisma = new PrismaClient();
