FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install || true
COPY . .
RUN npm run build || true
EXPOSE 3000
ENV BACKEND_URL=http://backend:8000
CMD ["npm","run","start"]
