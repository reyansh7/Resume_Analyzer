import { Router } from "express";
import { analyzeResumeController, analyzeResumeV2Controller } from "../controllers/resume.controller";
import { optionalAuthMiddleware } from "../middleware/auth.middleware";
import { upload } from "../middleware/upload.middleware";

const router = Router();

// Public endpoints - optional auth for resume analysis
router.post("/analyze", optionalAuthMiddleware, upload.single("resume"), analyzeResumeController);
router.post("/analyze/v2", optionalAuthMiddleware, upload.single("resume"), analyzeResumeV2Controller);

export default router;
