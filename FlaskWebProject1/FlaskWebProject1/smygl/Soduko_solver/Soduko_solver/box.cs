using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Soduko_solver
{
    class box
    {
        private int[,] _data;
        private bool[] _check;

        public box()
        {
            _data = new int[3, 3];
            _check = new bool[9];
        }

        public bool checkValid()
        {
            for (int i = 0; i < 9; i++)
            {
                if (!this._check[i])
                {
                    return false;
                }
            }
            return true;
        }

        public int count()
        {
            int counter = 0;
            for (int i = 0; i < 3; i++)
            {
                for (int ii = 0; ii < 3; ii++)
                {
                    if (this._data[i,ii] != 0)
                    {
                        counter++;
                    }
                }
            }
            return counter;
        }

        public void set(int[] index, int data)
        {
            this._data[index[0], index[1]] = data;
            this._check[data-1] = true;
        }

        public void remove(int[] index)
        {
            if (this._data[index[0],index[1]] == 0)
            {
                return;
            }
            this._check[this._data[index[0],index[1]] - 1] = false;
            this._data[index[0], index[1]] = 0;
        }

        public bool check(int num)
        {
            for (int i = 0; i < 3; i++)
            {
                for (int ii = 0; ii < 3; ii++)
                {
                    if (this._data[i, ii] == num)
                    {
                        return false;
                    }
                }
            }
            return true;
        }
    }
}
