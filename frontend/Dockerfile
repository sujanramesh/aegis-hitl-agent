# ---------- Build stage ----------
    FROM node:20-alpine AS build

    WORKDIR /app
    
    COPY package.json package-lock.json ./
    
    RUN npm ci
    
    COPY . .
    
    ARG VITE_API_BASE_URL=/api
    ARG VITE_APP_ENV=Production
    
    ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
    ENV VITE_APP_ENV=$VITE_APP_ENV
    
    RUN npm run build
    
    
    # ---------- Production stage ----------
    FROM nginx:alpine
    
    COPY nginx.conf /etc/nginx/conf.d/default.conf
    
    COPY --from=build /app/dist /usr/share/nginx/html
    
    EXPOSE 80
    
    HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
        CMD wget --quiet --tries=1 --spider http://127.0.0.1/ || exit 1
    
    CMD ["nginx", "-g", "daemon off;"]