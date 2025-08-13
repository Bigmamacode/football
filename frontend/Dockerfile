FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json* yarn.lock* pnpm-lock.yaml* ./
RUN if [ -f yarn.lock ]; then yarn;     elif [ -f pnpm-lock.yaml ]; then corepack enable && pnpm i;     else npm i; fi
COPY . .
RUN npm run build || yarn build || pnpm build
EXPOSE 3000
CMD ["npm", "run", "start"]
