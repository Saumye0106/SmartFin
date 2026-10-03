# SmartFin frontend: build the React app, then serve it with nginx.
#   docker build -t smartfin-frontend frontend

FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Same address for the site and the API (nginx forwards API calls), and absolute asset paths
# so reloading a deep link such as /profile/edit still finds /assets/...
ENV VITE_API_BASE_URL="" \
    VITE_BASE="/"
RUN npm run build


FROM nginx:1.29-alpine AS runtime
COPY proxy_params_smartfin /etc/nginx/proxy_params_smartfin
# The official image fills ${BACKEND_URL} into this template at start-up.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
ENV BACKEND_URL=http://backend:5000 \
    NGINX_ENVSUBST_FILTER=BACKEND_URL
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD wget -qO- http://127.0.0.1/nginx-health || exit 1
