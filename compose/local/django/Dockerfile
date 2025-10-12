
# define an alias for the specific python version used in this file.
FROM vikasy/hirethon-base:latest

ARG BUILD_ENVIRONMENT=local
ARG APP_HOME=/app
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV BUILD_ENV ${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

RUN addgroup --system django \
    && adduser --system --ingroup django django

COPY ./requirements .
RUN pip install -r ${BUILD_ENVIRONMENT}.txt

# copy application code to WORKDIR
COPY --chown=django:django . ${APP_HOME}

# make django owner of the WORKDIR directory as well.
RUN chown django:django ${APP_HOME}

# Copy entrypoint and start scripts, make sure they are executable
# Copy entrypoint and start scripts, make sure they are executable
COPY --chown=django:django ./compose/local/django/entrypoint /entrypoint
COPY --chown=django:django ./compose/local/django/start /start
COPY --chown=django:django ./compose/local/django/celery/worker/start /start-celeryworker
COPY --chown=django:django ./compose/local/django/celery/beat/start /start-celerybeat
RUN chmod +x /start-celeryworker /start-celerybeat
RUN chmod +x /entrypoint /start

ENTRYPOINT ["/entrypoint"]
