import transporter from "../lib/emailService.js";
import { generateToken } from "../lib/utils.js";
import OTP from "../model/OTP.model.js";
import User from "../model/User.models.js";
import bcrypt from "bcryptjs";
import { scheduleUserDeletion } from "../queues/userqueues.js";
import dotenv from "dotenv";
dotenv.config();


export const signup = async (req, res) => {
    try {
        const { fullname, email, password } = req.body;

        if (!fullname || !email || !password) {
            return res.status(400).json({ message: "All fields are required" });
        }

        if (password.length < 8) {
            return res.status(400).json({ message: "Password must be atleast 8 characters long" });
        }



        const user = await User.findOne({ email });

        //userid
        let userId = user?._id;

        if (user && user.isVerified) {
            return res.status(400).json({ message: "User already exists" });
        }

        if (!user) {
            const salt = await bcrypt.genSalt(10);
            const hashedPassword = await bcrypt.hash(password, salt);

            const newUser = await User.create({
                fullname,
                email,
                password: hashedPassword
            });

            if (!newUser) {
                console.log("user creation failed");
                return res.status(500).json({ message: "Something went Wrong" });
            }

            userId = newUser?._id;
            // generateToken(userId, res);

            await scheduleUserDeletion(userId);
        }
        generateToken(userId, res);
        console.log("userId", userId);
        
        return res.status(200).json({ message: "User registered. Please verify your email." });

    } catch (error) {
        console.log("error in auth.controller.js/signup", error);
        return res.status(500).json({ message: "Internal server error" });
    }
}

export const login = async (req, res) => {
    try {
        const { email, password } = req.body;
        if (!email || !password) {
            return res.status(400).json({ message: "All fields are required" });
        }
        const user = await User.findOne({ email });
        if (!user) {
            return res.status(400).json({ message: "invalid credentials" });
        }
        const isPasswordMatched = await bcrypt.compare(password, user.password);
        if (!isPasswordMatched) {
            return res.status(400).json({ message: "invalid credentials" });
        }

        generateToken(user._id,res);

        return res.status(200).json({
            _id: user._id,
            fullname: user.fullname,
            email: user.email
        })

    } catch (error) {
        console.log("error in auth.controller.js/login", error);
        return res.status(500).json({ message: "Internal server error" });
    }
}

export const logout = async (req, res) => {
    try {
        res.cookie("jwt", "", { maxAge: 0 });
        return res.status(200).json({ message: "logged out successfully" });
    } catch (error) {
        console.log("error in auth.controller.js/logout", error);
        return res.status(500).json({ message: "Internal server error" });
    }
}

export const sendOTP = async (req, res) => {
    try {
        const userId = req.user._id;

        let isOtpupdated = false;

        const otp = Math.floor(100000 + Math.random() * 900000).toString();

        const userOtp = await OTP.findOne({ userId });

        const user = await User.findById(userId);

        if (!userOtp && user) {
            const newOtp = await OTP.create({
                userId,
                otp
            });
            if (!newOtp) {
                return res.status(500).json({ message: "Failed create OTP" });
            }
            isOtpupdated = true;
        }


        if (!user) {
            return res.status(404).json({ message: "User not found" });
        }

        if (!isOtpupdated) {

            const updateOtp = await OTP.findByIdAndUpdate(
                userOtp._id,
                { otp },
                { new: true });

                console.log("updateOtp",updateOtp);
            if (!updateOtp) {
                return res.status(500).json({ message: "Failed update OTP" });
            }
        }

        const email = user.email;

        // if (userOtp && user) {
        //     const jsonotp = userOtp.toObject();
        //     const jsonuser = user.toObject();

        //     email = jsonuser.email;
        //     otp = jsonotp.otp;
        // } else {
        //     return res.status(404).json({ message: "OTP not generated" });
        // }

        console.log("userOtp", userOtp);
        console.log("email", email);

        const mailOptions = {
            from: process.env.EMAIL,
            to: email,
            subject: "Your OTP Code",
            text: `Your OTP is: ${otp}. It will expire in 5 minutes.`,
        };

        await transporter.sendMail(mailOptions);

        return res.status(200).json({ message: "OTP sent successfully" });
    } catch (error) {
        console.log("error in auth.controller.js/sendOTP", error);
        return res.status(500).json({ message: "Internal server error" });
    }

}

export const verifyOTP = async (req, res) => {
    try {
        const { otp } = req.body;
        const userId = req.user._id;
        const userOtp = await OTP.findOne({ userId, otp });
        console.log("userOtp", userOtp);
        if (userOtp) {
            const upadtedUser = await User.findByIdAndUpdate(userId, { isVerified: true }, { new: true }).select("-password");
            return res.status(200).json(upadtedUser);
        }
        else {
            return res.status(400).json({ message: "Invalid OTP" });
        }
    } catch (error) {
        console.log("error in auth.controller.js/verifyOTP", error);
        return res.status(500).json({ message: "Internal server error" });

    }
}

export const checkAuth = async (req, res) => {
    try {
        if(req.user.isVerified){
            return res.status(200).json(req.user);
        }
        else return res.status(401).json({ message: "Unauthorized" });
    } catch (error) {
        console.log("error in auth.controller.js/checkAuth", error);
        res.status(500).json({ message: "Internal server error" });
    }
}

