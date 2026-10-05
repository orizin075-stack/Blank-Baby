from tukuyo_v895.promotion import verify_external_promotion
def test_self_or_garbage_rejected(): assert not verify_external_promotion({'payload':{},'signature_b64':''},'zKiE5apfYjWlPaQhA4oS+I6j2nS8HwIvWzOQ3SXHNBk=','00'*32)
