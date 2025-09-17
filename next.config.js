/** @type {import('next').NextConfig} */
module.exports={experimental:{appDir:true},env:{BACKEND_URL:process.env.BACKEND_URL||'http://localhost:8000'}};
