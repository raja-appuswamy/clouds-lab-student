# Multi-stage build for the echo bot.
#   Stage 1 (builder) installs the Python deps into a throwaway layer.
#   Stage 2 (runtime) is a slim image that copies only the installed packages + app.
# The two stages keep the final image small (target < 400 MB) — inspect it with
# `docker images` and discuss the size in your report.
#
# Two lines are left for YOU to complete (search for TODO).

# ---- Stage 1: builder ----
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
# TODO: install the requirements into the prefix /install so stage 2 can copy them.
#       Hint: pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Stage 2: runtime ----
FROM python:3.11-slim
WORKDIR /app
# Bring in the packages installed in the builder (site-packages + console scripts).
COPY --from=builder /install /usr/local
COPY app.py .
ENV PORT=8080
EXPOSE 8080
# TODO: set the CMD to launch gunicorn, binding 0.0.0.0:8080 and serving "app:app".
#       Use the JSON/exec form: CMD ["gunicorn", "--bind", "0.0.0.0:8080", ...]
