const dontenv = require('dotenv');
dontenv.config();
const db = require('./db');

const express = require('express');
const router = express.Router();
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');


const JWT_SECRET = process.env.JWT_SECRET;

const registerStud = async (req, res) => {
    const {roll_no, stud_name, email, password, stud_div, stud_dept } = req.body;
    try{
        const hashPass = await bcrypt.hash(password, 10);
        await db.query('BEGIN');
        await db.query('INSERT INTO student_data (roll_no, name, email, password) VALUES ($1, $2, $3, $4)', [roll_no, stud_name, email, hashPass]);
        // await db.query('INSERT INTO student_info (roll_no, stud_name, stud_div, stud_dept) VALUES ($1, $2, $3, $4)', [roll_no, stud_name, stud_div, stud_dept]);
        await db.query('COMMIT');
        res.status(201).json({ message: 'User registered successfully' });
    } catch (error) {
        await db.query('ROLLBACK');
        console.error('Error occurred while registering user:', error);
        res.status(500).json({ message: 'Internal server error' });

    }
}

const loginStud = async (req, res) => {
    const { email, password } = req.body;

    try {
        const result = await db.query('SELECT student_data.email, student_data.roll_no,student_data.name, student_data.password, student_info.stud_dept, student_info.stud_div FROM student_data JOIN student_info ON student_data.roll_no = student_info.roll_no WHERE student_data.email = $1', [email]);
        if (result.rows.length === 0) {
            return res.status(401).json({ message: 'Invalid email or password' });
        }

    
        const user = result.rows[0];
        const isPassValid = await bcrypt.compare(password, user.password);
        if(!isPassValid){
            return res.status(401).json({ message: 'Invalid email or password' });
        }
         const token = jwt.sign({email : user.email, roll_no: user.roll_no, role: "student", stud_dept: user.stud_dept, stud_div: user.stud_div}, JWT_SECRET, {expiresIn: '1h'});
         res.cookie('token', token, {httpOnly: true, secure: process.env.NODE_ENV === 'production', maxAge: 3600000});

        return res.status(200).json({ message: 'Login successful', token, student:{
            roll_no: user.roll_no,
            name: user.name,
            email: user.email,
            stud_dept: user.stud_dept,
            stud_div: user.stud_div
        } });


    } catch (error) {
        console.error('Error occurred while logging in:', error);
        return res.status(500).json({ message: 'Internal server error' });
    }

}

const registerFac = async (req, res) => {
    const{fac_id, fac_name, fac_dept, email, password } = req.body;

    try{
        const hashPass = await bcrypt.hash(password, 10);

        await db.query('INSERT INTO faculty_info (fac_id, fac_name, fac_dept, email, password) VALUES ($1, $2, $3, $4, $5)', [fac_id, fac_name, fac_dept, email, hashPass]);
        res.status(201).json({ message: 'User registered successfully' });
    }catch (error) {
        console.error('Error occurred while registering user:', error);
        res.status(500).json({ message: 'Internal server error' });
    }

}

const loginFac = async (req, res) => {
    const {email, password} = req.body;
    try {
        const result = await db.query('SELECT * FROM faculty_info WHERE email = $1', [email]);
        if (result.rows.length === 0) {
            return res.status(401).json({ message: 'Invalid email or password' });
        }
        const user = result.rows[0];
        const isPassValid = await bcrypt.compare(password, user.password);
        if(!isPassValid){
            return res.status(401).json({ message: 'Invalid email or password' });
        }

        const token = jwt.sign({fac_id : user.fac_id, email : user.email, role: "faculty", fac_dept : user.fac_dept}, JWT_SECRET, {expiresIn: '1h'});
        res.cookie('token', token, {httpOnly: true, secure: process.env.NODE_ENV === 'production', maxAge: 3600000});

         return res.status(200).json({ message: 'Login successful', token, faculty:{
            fac_id: user.fac_id,
            fac_dept: user.fac_dept,
            name: user.fac_name,
            email: user.email
        
         }});


        res.status(200).json({message: 'Login successful', token});



    }catch (error) {
        console.error('Error occurred while logging in:', error);
        return res.status(500).json({ message: 'Internal server error' });
    }
}


const logout = (req, res) => {
    
    res.clearCookie('token', {httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict'});
    res.status(200).json({ message: 'Logout successful' });
}

module.exports = {
  loginStud,
  loginFac,
  registerStud,
  registerFac,
  logout
};