class Scrambler:
    '''This class provides a reversible bijective mapping between the numbers
    in range(2**16) and strings representing hex values of the numbers in the
    same range.

    This allows us to give a unique non-sequential ID to 2**16 model instances.

    >>> scrambler = Scrambler(100)
    >>> scrambler.forward(1)
    '92AD'
    >>> scrambler.backward('92AD')
    1
    '''
    def __init__(self, offset):
        n = 16
        N = 2 ** n
        m = sum(2 ** i for i in range(n) if i % 3 == 0)
        s = (n - 1) // 4 + 1

        assert N % m != 0

        self.inp_to_outp = {}
        self.outp_to_inp = {}

        for inp in range(N):
            outp = format((m * inp + offset) % N, f'0>{s}x').upper()
            self.inp_to_outp[inp] = outp
            self.outp_to_inp[outp] = inp

        assert len(self.inp_to_outp) == N
        assert len(self.outp_to_inp) == N

    def forward(self, inp):
        return self.inp_to_outp[inp]

    def backward(self, outp):
        return self.outp_to_inp[outp]
