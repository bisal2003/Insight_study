import express from 'express';
import { checkAuth, login, logout, sendOTP, signup, verifyOTP } from '../controller/auth.controller.js';
// import { protectSignup } from '../middleware/otp.middleware.js';
import { protectroute } from '../middleware/auth.middleware.js';

const router = express.Router();

router.post("/signup",signup);

router.post("/signup/request-otp",protectroute,sendOTP);

router.post("/login",login);

router.post("/logout",logout);

router.post("/signup/verify-otp",protectroute,verifyOTP);

router.get("/check",protectroute,checkAuth)

export default router;