#include <iostream>
using namespace std;
class student
{
protected:
    int Id;

public:
    set_Id(int a)
    {
        Id = a;
    }
    show_Id()
    {
        cout << "Student ID: " << Id << endl;
    }
};
class subject : public student
{
protected:
    int OOPS;
    int DSA;

public:
    set_marks(float a, float b)
    {
        OOPS = a;
        DSA = b;
    }
    show_marks()
    {
        cout << "Marks of OOPS:" << OOPS << endl;
        cout << "Marks of DSA:" << DSA << endl;
    }
};
class Result : public subject
{
private:
    float percentage = (OOPS + DSA) / 2;

public:
    show_Result()
    {
        show_Id();
        show_marks();
        cout << "Percentage of " << Id << ": " << (OOPS + DSA) / 2 <<" % "<< endl;
    }
};
int main()
{
    Result Akhil;
    cout<<"Student Name : Akhil Kushwaha"<<endl;
    Akhil.set_Id(9398);
    Akhil.set_marks(45,49);
    Akhil.show_Result();
    return 0;
}