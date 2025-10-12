
# define an alias for the specific python version used in this file.
FROM cookiecutter-django-base:latest

ARG BUILD_ENVIRONMENT=production
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
COPY --chown=django:django ./compose/production/django/entrypoint /entrypoint
COPY --chown=django:django ./compose/production/django/start /start
COPY --chown=django:django ./compose/production/django/celery/worker/start /start-celeryworker
COPY --chown=django:django ./compose/production/django/celery/beat/start /start-celerybeat
RUN chmod +x /entrypoint /start /start-celeryworker /start-celerybeat

USER django

ENTRYPOINT ["/entrypoint"]
