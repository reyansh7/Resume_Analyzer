import { Router } from "express";
import { saveOnboardingController } from "../controllers/onboarding.controller";
import { authMiddleware } from "../middleware/auth.middleware";

const router = Router();

router.post("/", authMiddleware, saveOnboardingController);

export default router;
