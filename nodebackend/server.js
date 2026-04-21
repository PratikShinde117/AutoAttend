require("dotenv").config();

const express = require('express');
const cors = require('cors');
const app = express();
const port = 3000;
const modelRoutes = require("./routes/modelRoutes.js");
const fileUpload = require("express-fileupload");
const cookieParser = require("cookie-parser");

app.use(cors());
app.use(express.json());
app.use(cookieParser());


app.use(fileUpload());

app.use("/", modelRoutes);

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});