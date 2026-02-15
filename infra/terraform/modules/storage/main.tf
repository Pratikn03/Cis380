resource "aws_s3_bucket" "uploads" {
  bucket_prefix = "${var.project}-${var.environment}-uploads-"
}

resource "aws_s3_bucket_versioning" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  versioning_configuration {
    status = "Enabled"
  }
}
