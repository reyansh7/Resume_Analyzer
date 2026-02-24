import { Router } from "express";
import { analyzeResumeController } from "../controllers/resume.controller";
import { authMiddleware } from "../middleware/auth.middleware";
import { upload } from "../middleware/upload.middleware";

const router = Router();

router.post("/analyze", authMiddleware, upload.single("resume"), analyzeResumeController);

export default router;
