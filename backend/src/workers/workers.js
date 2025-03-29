import { redisConfig,Worker } from "../config/redis.js";
import User from "../model/User.models.js";


// Create a worker that listens to the 'userDeletionQueue'
export const userDeletionWorker = new Worker(
  "userDeletionQueue",
  async (job) => {
    const { userId } = job.data;

    // Check if user exists and is still unverified/
    const user = await User.findById(userId);
    if (user && !user.isVerified) {
      await User.findByIdAndDelete(userId);
      console.log(`Deleted unverified user: ${user.email}`);
      
    }
  },
  
  redisConfig
);

console.log("User deletion worker started.");
