# Landing estática de Casewright servida con nginx (versión estable, tag fijo).
FROM nginx:1.30.7-alpine

COPY index.html /usr/share/nginx/html/index.html

# wget viene con busybox en la imagen alpine.
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=5 \
    CMD wget -q --spider http://127.0.0.1/ || exit 1
