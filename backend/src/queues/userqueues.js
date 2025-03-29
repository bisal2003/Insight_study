import {Queue,redisConfig} from "../config/redis.js"

// Create a queue named 'userDeletionQueue'
const userDeletionQueue = new Queue("userDeletionQueue", redisConfig);

/**
 * Add a user to the deletion queue, scheduled for 5 minutes later.
 * @param {string} userId - The ID of the user to delete.
 */
export const scheduleUserDeletion = async (userId) => {
  await userDeletionQueue.add(
    "deleteUser",
    { userId },
    { delay: 5 * 60 * 1000 } // 5 minutes delay
  );
  console.log(`User ${userId} scheduled for deletion in 5 minutes.`);
};


