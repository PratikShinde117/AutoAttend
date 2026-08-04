const dotenv = require("dotenv");
dotenv.config();
const {loginStud, loginFac, registerStud, registerFac, logout} = require("../login.js");
const express = require("express");
const router = express.Router();
const authMiddleware = require("../middlewares/authMiddleware.js");
const axios = require("axios");

router.post("/register-student", registerStud);
router.post("/login-student", loginStud);
router.post("/register-faculty", registerFac);
router.post("/login-faculty", loginFac);
router.post("/logout", authMiddleware(), logout);


router.post("/camera-on", authMiddleware(["faculty"]), async(req, res) => 
    {
        console.log("TOKEN IN ROUTE:", req.token);
        
        try{
            console.log(req.body.subject);
            const response = await axios.post("http://127.0.0.1:5000/camera-on", {subject : req.body.subject, division: req.body.division}, 
                {headers: {Authorization: `Bearer ${req.token}`, "x-internal-key": process.env.INTERNAL_API_KEY}});
            res.json(response.data);
        }
        catch(err){
            console.log("AXIOS ERROR:", err.message);

    if (err.response) {
        console.log("FLASK RESPONSE:", err.response.data);
        return res.status(err.response.status).json(err.response.data);
    }

    res.status(500).json({ error: "Failed to turn camera on" });
        }
    })

router.post("/camera-off", authMiddleware(["faculty"]), async(req, res) => {
    try{
        const response = await axios.post("http://127.0.0.1:5000/camera-off",{} ,{headers: {Authorization: `Bearer ${req.token}`, "x-internal-key": process.env.INTERNAL_API_KEY} });
        res.json(response.data);
    }
    catch(err){
        res.status(500).json({error: "Failed to turn camera off"});
    }
})

router.post(
  "/add-face",
  authMiddleware(["faculty"]),
  async (req, res) => {
    try {
      const { roll_no, stud_name, stud_dept, stud_div } = req.body;

      // basic validation
      if (!roll_no || !stud_name || !stud_dept || !stud_div) {
        return res.status(400).json({
          error: "roll_no, stud_name, stud_dept, and stud_div are required"
        });
      }

      console.log("SENDING TO FLASK:", { roll_no, stud_name, stud_dept, stud_div });

      const response = await axios.post(
        "http://127.0.0.1:5000/add-face",
        {
          roll_no,
          stud_name,
          stud_dept,
          stud_div
        },
        {
          headers: {
            Authorization: `Bearer ${req.token}`,
            "x-internal-key": process.env.INTERNAL_API_KEY
          }
          
        }
      );

      res.json(response.data);

    } catch (err) {
      console.log("AXIOS ERROR:", err.message);

      if (err.response) {
        console.log("FLASK RESPONSE:", err.response.data);
        return res.status(err.response.status).json(err.response.data);
      }

      res.status(500).json({ error: "Failed to add face" });
    }
  }
);


router.post("/attendance-report", authMiddleware(["faculty"]), async(req, res) => {
    try{
        const {subject, division} = req.body;
        console.log("SUBJECT & DIVISION IN ROUTE:", subject, division);
        console.log("Faculty DEPT:", req.user.fac_dept);
        if(!subject || !division){
            return res.status(400).json({error: "Subject and division are required"});
        }
        console.log("CALLING FLASK...");
        const response = await axios.post("http://127.0.0.1:5000/attendance-report", {subject, division}, {headers: {Authorization: `Bearer ${req.token}`, "x-internal-key": process.env.INTERNAL_API_KEY} });
        console.log("FLASK RESPONSE:", response.data);
        res.json(response.data);
    }
  
    catch(err){
       console.log("AXIOS ERROR:", err.response?.data || err.message);

        
        if (err.response) {
            return res.status(err.response.status).json(err.response.data);
        }

        res.status(500).json({ error: "Failed to generate attendance report" });
    }
})


router.get("/student-attendance", authMiddleware(["student"]), async(req, res) => {
    try{
        
        const response = await axios.get(`http://127.0.0.1:5000/student-attendance`, {
            headers: {
                Authorization: `Bearer ${req.token}`,
                "x-internal-key": process.env.INTERNAL_API_KEY
            }
            
        });
        res.json(response.data);
    }
    catch(err){
        console.log("AXIOS ERROR:", err.message);
        res.status(500).json({ error: "Failed to fetch student attendance" });

    }
})

router.post("/download-report", authMiddleware(["faculty"]), async(req, res) => {
    try{
        const {subject, division} = req.body; 
        if(!subject || !division){
            return res.status(400).json({error: "Subject and division are required"});
        }
        const response = await axios.post("http://127.0.0.1:5000/download-report", {subject, division}, {headers: {Authorization: `Bearer ${req.token}`, "x-internal-key": process.env.INTERNAL_API_KEY}, responseType: 'stream'});
        

        res.setHeader(
            "Content-Disposition",
            response.headers["content-disposition"]
        );

        res.setHeader(
            "Content-Type",
            response.headers["content-type"]
        );

        //  pipe file
        response.data.pipe(res);



    }catch(err){
        console.log("AXIOS ERROR:", err.message);
        res.status(500).json({ error: "Failed to download attendance report" });
    }
}
)


router.get("/student-sessions", authMiddleware(["student"]), async(req, res) => {
    try{
        const response = await axios.get(`http://127.0.0.1:5000/student-sessions`, {
            headers: {
                Authorization: `Bearer ${req.token}`,
                "x-internal-key": process.env.INTERNAL_API_KEY
            }
        });
        res.json(response.data);
    }
    catch(err){
        console.log("AXIOS ERROR:", err.message);
        res.status(500).json({ error: "Failed to fetch student sessions" });
    }
});


const FormData = require("form-data");

router.post("/mark-attendance-request", authMiddleware(["student"]), async (req, res) => {
    try {
        const { session_id, reason } = req.body;
        const file = req.files?.letter; // assuming you're using express-fileupload or multer
        console.log("BODY:", req.body);
console.log("FILES:", req.files);

        if (!session_id || !reason || !file) {
            return res.status(400).json({
                error: "session_id, reason and letter are required"
            });
        }

        const formData = new FormData();
        formData.append("session_id", session_id);
        formData.append("reason", reason);
        formData.append("letter", file.data, {
  filename: file.name,
  contentType: file.mimetype
});

        const response = await axios.post(
            "http://127.0.0.1:5000/mark-attendance-request",
            formData,
            {
                headers: {
                    ...formData.getHeaders(),
                    Authorization: `Bearer ${req.token}`,
                    "x-internal-key": process.env.INTERNAL_API_KEY
                }
            }
        );

        res.json(response.data);

    } catch (err) {
        console.log("AXIOS ERROR:", err.response?.data || err.message);

        if (err.response) {
            return res.status(err.response.status).json(err.response.data);
        }

        res.status(500).json({
            error: "Failed to submit attendance request"
        });
    }
});


router.get("/attendance-requests", authMiddleware(["faculty"]), async(req, res) => {
  try{
    const response = await axios.get("http://127.0.0.1:5000/attendance-requests", {
      headers: {
        Authorization: `Bearer ${req.token}`,
        "x-internal-key": process.env.INTERNAL_API_KEY
      }
    });
    res.json(response.data);

  }catch(err){
    console.log("AXIOS ERROR:", err.response?.data || err.message); 
    res.status(500).json({ error: "Failed to fetch attendance requests" });
  }

})


router.patch("/attendance-requests/:request_id", authMiddleware(["faculty"]), async (req, res) => {
    try {
        const { request_id } = req.params;
        const { status } = req.body;

        const response = await axios.patch(
            `http://127.0.0.1:5000/attendance-requests/${request_id}`,
            { status },
            {
                headers: {
                    Authorization: `Bearer ${req.token}`,
                    "x-internal-key": process.env.INTERNAL_API_KEY
                }
                
            }
        );

        res.json(response.data);

    } catch (err) {
        console.log(err.response?.data || err.message);
        res.status(500).json({ error: "Failed to update request" });
    }
});

module.exports = router;