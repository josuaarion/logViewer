using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Soduko_solver
{
    class bord
    {
        private cell[,] bordid;
        private int[,] values;
        public bord(cell[,] bordid)
        {
            this.bordid = bordid;
            this.values = new int[9,9];
        }

        public string getValue(int[] index)
        {
            return values[index[0], index[1]].ToString();
        }

        public bool isOccu(int[] index)
        {
            if (values[index[0], index[1]] == 0)
            {
                return false;
            }
            return true;
        }

        public int[] findBestCell()
        {
            int best = 0;
            int[] index = new int[] {0,-1};

            for (int i = 0; i < 9; i++)
            {
                for (int ii = 0; ii < 9; ii++)
                {
                    if (this.values[i,ii] == 0) { 
                    
                        if (this.bordid[i,ii].countRef() > best)
                        {
                            best = this.bordid[i, ii].countRef();
                            index = new int[] {i,ii};
                        }
                    }
                }
            }
            return index;
        }

        public void removeValue(int[] index)
        {
            int row, col;

            if (index[0] == 0 || index[0] == 3 || index[0] == 6)
            {
                row = 0;
            }
            else if(index[0] == 1 || index[0] == 4 || index[0] == 7)
            {
                row = 1;
            }
            else
            {
                row = 2;
            }
            if (index[1] == 0 || index[1] == 3 || index[1] == 6)
            {
                col = 0;
            }
            else if (index[1] == 1 || index[1] == 4 || index[1] == 7)
            {
                col = 1;
            }
            else
            {
                col = 2;
            }

            int[] innerIndex = { row, col };

            this.bordid[index[0], index[1]].removeValue(index[1], index[0], innerIndex);
            this.values[index[0], index[1]] = 0;
        }

        public void setValue(int[] index, int value){

            
            int row, col;

            if (index[0] == 0 || index[0] == 3 || index[0] == 6)
            {
                row = 0;
            }
            else if (index[0] == 1 || index[0] == 4 || index[0] == 7)
            {
                row = 1;
            }
            else
            {
                row = 2;
            }
            if (index[1] == 0 || index[1] == 3 || index[1] == 6)
            {
                col = 0;
            }
            else if (index[1] == 1 || index[1] == 4 || index[1] == 7)
            {
                col = 1;
            }
            else
            {
                col = 2;
            }

            int[] innerIndex = {row,col};
            
            this.bordid[index[0], index[1]].setValue(index[1], index[0], innerIndex, value);
            this.values[index[0], index[1]] = value;
        }

        public bool check(int[] index, int value)
        {
            if (this.bordid[index[0], index[1]].checkValid(value))
            {
                return true;
            }
            return false;
        }

        //returns true if it is solved
        public bool isSolved()
        {
            for (int i = 0; i < 9; i++)
            {
                for (int ii = 0; ii < 9; ii++)
                {
                    if (values[i, ii] == 0)
                    {
                        return false;
                    }
                }
            }

            for (int i = 0; i < 9; i++)
            {
                for (int ii = 0; ii < 9; ii++)
                {
                    if (!this.bordid[i, ii].isSolved())
                    {
                        return false;
                    }
                }
            }
            return true;
        }

        public bool isFull()
        {
            for (int i = 0; i < 9; i++)
            {
                for (int ii = 0; ii < 9; ii++)
                {
                    if (values[i, ii] == 0)
                    {
                        return false;
                    }
                }
            }
            return true;

        }

        public bool isValid()
        {
            for (int i = 0; i < 9; i++)
            {
                for (int ii = 0; ii < 9; ii++)
                {
                    int[] c = {i,ii};
                    int val = values[i, ii];
                    this.removeValue(c);
                    if (!this.check(c, val) && val != 0)
                    {
                        this.setValue(c, val);
                        return false;
                    }
                    if (val != 0)
                    {
                        this.setValue(c, val);
                    }
                }
            }
            return true;
        }
    }
}
