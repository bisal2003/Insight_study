import mongoose from "mongoose";

const OTPSchema = new mongoose.Schema({
    userId:{
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true,
    },
    otp:{
        type: String,
        required: true,
    },
    createdAt: { type: Date, default: Date.now, expires: 300 }, // Auto-delete after 5 mins
});

const OTP = mongoose.model('OTP', OTPSchema);
export default OTP;