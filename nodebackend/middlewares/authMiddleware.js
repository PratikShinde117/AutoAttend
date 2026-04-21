const jwt = require("jsonwebtoken");

const authMiddleware = (roles = []) => {
return (req, res, next) => {
    try{
        const token = req.cookies?.token || req.headers.authorization?.split(" ")[1];

        console.log("TOKEN RECEIVED IN MIDDLEWARE:", token);

        if(!token) return res.status(401).json({error: "No token provided"});

        const decoded = jwt.verify(token, process.env.JWT_SECRET);

       

        req.user = decoded;
        req.token = token;

        console.log("TOKEN SENT TO FLASK:", req.token);

         if (roles.length && !roles.includes(decoded.role)) {
        return res.status(403).json({ error: "Access denied" });
      }

        next();
    }
    catch(err){
        res.status(401).json({error: "Invalid token"});
 
    }
}
}
module.exports = authMiddleware;