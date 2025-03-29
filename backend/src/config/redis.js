import {Queue,Worker} from "bullmq";


const redisConfig = {
  connection: { host: "localhost", port: 6379 }, // Adjust if needed
};

export { redisConfig , Queue, Worker};
