import { Router } from "express";
import { analyzeResumeController, analyzeResumeV2Controller } from "../controllers/resume.controller";
import { authMiddleware } from "../middleware/auth.middleware";
import { upload } from "../middleware/upload.middleware";

const router = Router();

router.post("/analyze", authMiddleware, upload.single("resume"), analyzeResumeController);
router.post("/analyze/v2", authMiddleware, upload.single("resume"), analyzeResumeV2Controller);

export default router;
