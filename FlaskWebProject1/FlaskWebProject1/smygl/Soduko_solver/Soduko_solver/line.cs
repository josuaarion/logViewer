using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Soduko_solver
{
    class line
    {
        private int[] _data;
        private bool[] _check;

        public line()
        {
            _data = new int[9];
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

        public void set(int index, int data)
        {
            
            this._data[index] = data;
            this._check[data - 1] = true;
        }

        public int count()
        {
            int counter = 0;
            for (int i = 0; i < this._data.Length; i++)
            {
                if (this._data[i] != 0)
                {
                    counter++;
                }
            }
            return counter;
        }

        public void remove(int index)
        {
            if (this._data[index] == 0)
            {
                return;
            }
            this._check[this._data[index] - 1] = false;
            this._data[index] = 0;
        }

        public bool check(int num)
        {
            foreach (int item in this._data)
            {
                if (item == num)
                {
                    return false;
                }
            }
            return true;
        }
    }
}
