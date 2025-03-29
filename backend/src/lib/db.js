import moongose from 'mongoose';
import dotenv from 'dotenv';
dotenv.config();

export const  connectDB = async () => {
    try {
        const conn=await moongose.connect(process.env.MONGO_URI);
        console.log(`MongoDB connected: ${conn.connection.host}`);
    } catch (error) {
        console.log(`mongoDB connection error: ${error}`);
    }

}

