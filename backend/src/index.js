import express from 'express';
import dotenv from 'dotenv';
import cors from 'cors';
import { connectDB } from './lib/db.js';
import authroute from './route/auth.route.js';
import cookieParser from 'cookie-parser';
import { userDeletionWorker } from './workers/workers.js';

dotenv.config();

const app = express();

app.use(cors({
    origin: process.env.CORS_ORIGIN,
    credentials: true,
}))

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());

app.use('/api/v1/auth', authroute);

app.listen(process.env.PORT, () => {
  console.log('Server is running on http://localhost:5003');
  connectDB();
  userDeletionWorker;
});