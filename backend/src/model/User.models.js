import moongose from 'mongoose';

const UserSchema = new moongose.Schema({
    fullname: {
        type: String,
        required: true,
    },
    email:{
        type: String,
        required: true,
        unique: true,
    },
    password:{
        type: String,
        required: true,
        minlength:8,
    },
    isVerified:{
        type: Boolean,
        default: false,
    },
},{timestamps: true});

const User = moongose.model('User', UserSchema);
export default User;