import { Router } from "express";
import {
	loginController,
	logoutController,
	meController,
	registerController
} from "../controllers/auth.controller";
import { authMiddleware } from "../middleware/auth.middleware";

const router = Router();

router.post("/login", loginController);
router.post("/register", registerController);
router.get("/me", authMiddleware, meController);
router.post("/logout", logoutController);

export default router;
