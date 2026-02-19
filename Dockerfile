# FreeSurfer Docker image for processing
# Note: FreeSurfer requires a license file. Mount it at /opt/freesurfer/license.txt
FROM freesurfer/freesurfer:latest

# Install dcm2niix for DICOM conversion
RUN apt-get update && \
    apt-get install -y dcm2niix && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Default command
CMD ["/bin/bash"]
