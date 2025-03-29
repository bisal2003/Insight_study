import jwt from 'jsonwebtoken';
import dotenv from 'dotenv';
dotenv.config();

export const generateToken = (userId,res) => {
   const token=jwt.sign({userId},process.env.JWT_SECRET,{expiresIn:'7d'});
   res.cookie("jwt",token,{
    maxAge: 1000 * 60 * 60 * 24 * 7,
    httpOnly: true,
    secure:process.env.NODE_ENV !== 'development',
    sameSite:'strict'
   })
    return token;
}

