FROM mcr.microsoft.com/dotnet/sdk:10.0 AS tested
WORKDIR /src
ENV DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 DOTNET_GCHeapHardLimit=80000000
COPY . .
RUN dotnet test Jellyfin.sln --configuration Release --logger trx --results-directory /test-results -m:2 \
 && dotnet publish Jellyfin.Server/Jellyfin.Server.csproj --configuration Release --runtime linux-x64 --self-contained true --output /publish -m:2

# Preserve the deployed LinuxServer FFmpeg, Intel drivers, web client and init.
FROM lscr.io/linuxserver/jellyfin@sha256:0f42497a69fa0441bfd5f9d6bba8694f2a656ec984e571d0ac04c6dd91250039
ARG VCS_REF
LABEL org.opencontainers.image.source="https://github.com/dez011/jellyfin" \
      org.opencontainers.image.revision="${VCS_REF}"
RUN find /usr/lib/jellyfin/bin -mindepth 1 -delete
COPY --from=tested /publish/ /usr/lib/jellyfin/bin/
COPY --from=tested /test-results/ /homelab-test-results/
RUN /usr/lib/jellyfin/bin/jellyfin --version | grep -E '^Jellyfin.Server 12\.0\.0|^Jellyfin 12\.0\.0|^12\.0\.0'
